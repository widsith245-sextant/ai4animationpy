"""SOMA_HUMAN_BODY export helpers for UE and local AI4AnimationPy tooling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from pygltflib import (
    Accessor,
    Animation,
    AnimationChannel,
    AnimationChannelTarget,
    AnimationSampler,
    Asset,
    Attributes,
    Buffer,
    BufferView,
    GLTF2,
    Mesh,
    Node,
    Primitive,
    Scene,
    Skin,
)

from ai4animation.Animation.Hierarchy import Hierarchy
from ai4animation.Animation.Motion import Motion
from ai4animation.Export.GLBExporter import (
    _COMPONENT_FLOAT,
    _COMPONENT_UNSIGNED_SHORT,
    _TARGET_ARRAY_BUFFER,
    _TARGET_ELEMENT_ARRAY_BUFFER,
)
from ai4animation.Math import Quaternion, Transform


def _quat_normalize(q: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(q, axis=-1, keepdims=True)
    norms = np.where(norms < 1e-8, 1.0, norms)
    return q / norms


def _matrix_to_quaternion(matrix: np.ndarray) -> np.ndarray:
    return _quat_normalize(np.asarray(Quaternion.FromMatrix(matrix), dtype=np.float32))


def _extract_translation_rotation(matrices: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.asarray(Transform.GetPosition(matrices), dtype=np.float32),
        _matrix_to_quaternion(np.asarray(Transform.GetRotation(matrices), dtype=np.float32)),
    )


def _freeze_non_root_translations(
    animation_local_positions: np.ndarray,
    source_rest_local_positions: np.ndarray,
    bind_local_positions: np.ndarray,
    parent_indices: Sequence[int],
) -> np.ndarray:
    """Retarget local translations onto the SOMA bind hierarchy.

    Non-root joints keep bind offsets. Root joints carry only the delta from the
    source rest pose so the imported skeleton stays bound to the SOMA skin.
    """

    corrected = np.repeat(
        bind_local_positions[None, ...],
        animation_local_positions.shape[0],
        axis=0,
    ).astype(np.float32)

    root_indices = [index for index, parent_index in enumerate(parent_indices) if parent_index < 0]
    for root_index in root_indices:
        corrected[:, root_index] = bind_local_positions[root_index] + (
            animation_local_positions[:, root_index] - source_rest_local_positions[root_index]
        )

    return corrected


def _world_to_local_matrices(
    world_matrices: np.ndarray,
    parent_indices: Sequence[int],
) -> np.ndarray:
    world_matrices = np.asarray(world_matrices, dtype=np.float32)
    local_matrices = np.zeros_like(world_matrices)
    for bone_index, parent_index in enumerate(parent_indices):
        if parent_index < 0:
            local_matrices[..., bone_index, :, :] = world_matrices[..., bone_index, :, :]
        else:
            parent_world = world_matrices[..., parent_index, :, :]
            local_matrices[..., bone_index, :, :] = np.matmul(
                np.linalg.inv(parent_world),
                world_matrices[..., bone_index, :, :],
            )
    return local_matrices


def _compute_vertex_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    normals = np.zeros_like(vertices, dtype=np.float32)
    triangles = vertices[faces]
    face_normals = np.cross(
        triangles[:, 1] - triangles[:, 0],
        triangles[:, 2] - triangles[:, 0],
    )
    lengths = np.linalg.norm(face_normals, axis=1, keepdims=True)
    face_normals = np.divide(
        face_normals,
        np.where(lengths < 1e-8, 1.0, lengths),
    )
    for corner in range(3):
        np.add.at(normals, faces[:, corner], face_normals)
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    return np.divide(normals, np.where(lengths < 1e-8, 1.0, lengths)).astype(np.float32)


def _pad4(buffer: bytearray) -> None:
    while len(buffer) % 4 != 0:
        buffer.append(0)


class _BufferBuilder:
    def __init__(self) -> None:
        self.data = bytearray()
        self.buffer_views: list[BufferView] = []
        self.accessors: list[Accessor] = []

    def _add_buffer_view(self, byte_length: int, target: int | None = None) -> int:
        offset = len(self.data) - byte_length
        self.buffer_views.append(
            BufferView(
                buffer=0,
                byteOffset=offset,
                byteLength=byte_length,
                target=target,
            )
        )
        return len(self.buffer_views) - 1

    def add_vec_float(
        self,
        values: np.ndarray,
        components: int,
        *,
        target: int | None = None,
        with_minmax: bool = False,
    ) -> int:
        array = np.ascontiguousarray(values.astype(np.float32).reshape(-1, components))
        raw = array.tobytes()
        self.data.extend(raw)
        view_index = self._add_buffer_view(len(raw), target=target)
        _pad4(self.data)
        type_name = {2: "VEC2", 3: "VEC3", 4: "VEC4"}[components]
        self.accessors.append(
            Accessor(
                bufferView=view_index,
                byteOffset=0,
                componentType=_COMPONENT_FLOAT,
                count=int(array.shape[0]),
                type=type_name,
                min=array.min(axis=0).astype(float).tolist() if with_minmax else None,
                max=array.max(axis=0).astype(float).tolist() if with_minmax else None,
            )
        )
        return len(self.accessors) - 1

    def add_scalar_float(self, values: np.ndarray) -> int:
        array = np.ascontiguousarray(values.astype(np.float32).reshape(-1))
        raw = array.tobytes()
        self.data.extend(raw)
        view_index = self._add_buffer_view(len(raw))
        _pad4(self.data)
        self.accessors.append(
            Accessor(
                bufferView=view_index,
                byteOffset=0,
                componentType=_COMPONENT_FLOAT,
                count=int(array.shape[0]),
                type="SCALAR",
                min=[float(array.min())] if array.size else None,
                max=[float(array.max())] if array.size else None,
            )
        )
        return len(self.accessors) - 1

    def add_vec_uint16(
        self,
        values: np.ndarray,
        components: int,
        *,
        target: int | None = None,
    ) -> int:
        array = np.ascontiguousarray(values.astype(np.uint16).reshape(-1, components))
        raw = array.tobytes()
        self.data.extend(raw)
        view_index = self._add_buffer_view(len(raw), target=target)
        _pad4(self.data)
        type_name = {1: "SCALAR", 2: "VEC2", 3: "VEC3", 4: "VEC4"}[components]
        self.accessors.append(
            Accessor(
                bufferView=view_index,
                byteOffset=0,
                componentType=_COMPONENT_UNSIGNED_SHORT,
                count=int(array.shape[0]),
                type=type_name,
            )
        )
        return len(self.accessors) - 1

    def add_indices_uint16(self, values: np.ndarray) -> int:
        return self.add_vec_uint16(
            np.ascontiguousarray(values.astype(np.uint16).reshape(-1, 1)),
            1,
            target=_TARGET_ELEMENT_ARRAY_BUFFER,
        )

    def add_mat4_float(self, values: np.ndarray) -> int:
        matrices = np.ascontiguousarray(values.astype(np.float32).transpose(0, 2, 1))
        raw = matrices.tobytes()
        self.data.extend(raw)
        view_index = self._add_buffer_view(len(raw))
        _pad4(self.data)
        self.accessors.append(
            Accessor(
                bufferView=view_index,
                byteOffset=0,
                componentType=_COMPONENT_FLOAT,
                count=int(matrices.shape[0]),
                type="MAT4",
            )
        )
        return len(self.accessors) - 1


@dataclass(frozen=True)
class SOMAExportResult:
    glb_path: str
    motion_npz_path: str | None


def export_skinned_soma_glb(
    *,
    skin_npz_path: str,
    tpose_bvh_path: str,
    output_glb_path: str,
    animation_bvh_path: str | None = None,
    output_motion_npz_path: str | None = None,
    scale: float = 0.01,
) -> SOMAExportResult:
    """Export a SOMA skinned character GLB that UE can import as a source skeleton."""

    skin_npz = Path(skin_npz_path).resolve()
    tpose_bvh = Path(tpose_bvh_path).resolve()
    output_glb = Path(output_glb_path).resolve()

    if not skin_npz.exists():
        raise FileNotFoundError(f"SOMA skin file not found: {skin_npz}")
    if not tpose_bvh.exists():
        raise FileNotFoundError(f"SOMA T-pose BVH not found: {tpose_bvh}")

    payload = np.load(skin_npz, allow_pickle=True)
    vertices = np.asarray(payload["bind_vertices"], dtype=np.float32)
    faces = np.asarray(payload["faces"], dtype=np.int64)
    joint_names = [str(name) for name in payload["rig_joint_names"].tolist()]
    bind_global_without_root = np.asarray(payload["bind_rig_transform"], dtype=np.float32)
    skin_indices = np.asarray(payload["lbs_indices"], dtype=np.int32)
    skin_weights = np.asarray(payload["lbs_weights"], dtype=np.float32)

    normals = _compute_vertex_normals(vertices, faces)

    tpose_motion = Motion.LoadFromBVH(str(tpose_bvh), scale=scale)
    full_node_names = list(tpose_motion.Hierarchy.BoneNames)
    full_parent_indices = list(tpose_motion.Hierarchy.ParentIndices)
    if full_node_names[0] != "Root":
        raise ValueError("Expected SOMA BVH hierarchy to start with Root.")

    name_to_node_index = {name: index for index, name in enumerate(full_node_names)}
    missing_joint_names = [name for name in joint_names if name not in name_to_node_index]
    if missing_joint_names:
        raise ValueError(
            f"SOMA skin joints missing from BVH hierarchy: {missing_joint_names}"
        )

    export_node_names = list(joint_names)
    export_parent_indices: list[int] = []
    for joint_name in export_node_names:
        full_parent_name = tpose_motion.Hierarchy.ParentNames[name_to_node_index[joint_name]]
        export_parent_indices.append(
            export_node_names.index(full_parent_name) if full_parent_name in export_node_names else -1
        )

    joint_indices = [name_to_node_index[name] for name in export_node_names]
    bind_global = np.asarray(bind_global_without_root, dtype=np.float32)
    bind_local = _world_to_local_matrices(bind_global[None, ...], export_parent_indices)[0]
    bind_local_positions, bind_local_rotations = _extract_translation_rotation(bind_local)

    animation_motion = (
        tpose_motion
        if animation_bvh_path is None
        else Motion.LoadFromBVH(str(Path(animation_bvh_path).resolve()), scale=scale)
    )
    if list(animation_motion.Hierarchy.BoneNames) != full_node_names:
        raise ValueError("Animation BVH hierarchy does not match SOMA source hierarchy.")

    animation_world = np.asarray(animation_motion.GetBoneTransformations(), dtype=np.float32)[:, joint_indices]
    animation_local = _world_to_local_matrices(animation_world, export_parent_indices)
    animation_local_positions, animation_local_rotations = _extract_translation_rotation(animation_local)

    tpose_world = np.asarray(tpose_motion.GetBoneTransformations(), dtype=np.float32)[:, joint_indices]
    tpose_local = _world_to_local_matrices(tpose_world, export_parent_indices)[0]
    tpose_local_positions, tpose_local_rotations = _extract_translation_rotation(tpose_local)

    corrective_local = np.matmul(
        bind_local[:, :3, :3],
        np.linalg.inv(tpose_local[:, :3, :3]),
    ).astype(np.float32)
    corrective_local_quat = _matrix_to_quaternion(corrective_local)

    corrected_rotations = np.empty_like(animation_local_rotations, dtype=np.float32)
    for bone_index in range(len(export_node_names)):
        correction = corrective_local_quat[bone_index]
        bone_rotations = animation_local_rotations[:, bone_index]
        corrected_rotations[:, bone_index] = _quat_normalize(
            np.asarray(Quaternion.Multiply(correction, bone_rotations), dtype=np.float32)
        )

    corrected_positions = _freeze_non_root_translations(
        animation_local_positions=np.asarray(animation_local_positions, dtype=np.float32),
        source_rest_local_positions=tpose_local_positions,
        bind_local_positions=bind_local_positions,
        parent_indices=export_parent_indices,
    )

    num_vertices = int(vertices.shape[0])
    if num_vertices >= 65535:
        raise ValueError("SOMA mesh exceeds 16-bit index limits for this exporter.")

    joints_0 = skin_indices[:, :4]
    joints_1 = skin_indices[:, 4:8]
    weights_0 = skin_weights[:, :4]
    weights_1 = skin_weights[:, 4:8]
    weight_sums = weights_0.sum(axis=1, keepdims=True) + weights_1.sum(axis=1, keepdims=True)
    weights_0 = np.divide(weights_0, np.where(weight_sums < 1e-8, 1.0, weight_sums))
    weights_1 = np.divide(weights_1, np.where(weight_sums < 1e-8, 1.0, weight_sums))

    builder = _BufferBuilder()
    position_accessor = builder.add_vec_float(
        vertices,
        3,
        target=_TARGET_ARRAY_BUFFER,
        with_minmax=True,
    )
    normal_accessor = builder.add_vec_float(normals, 3, target=_TARGET_ARRAY_BUFFER)
    joints0_accessor = builder.add_vec_uint16(joints_0, 4, target=_TARGET_ARRAY_BUFFER)
    joints1_accessor = builder.add_vec_uint16(joints_1, 4, target=_TARGET_ARRAY_BUFFER)
    weights0_accessor = builder.add_vec_float(weights_0, 4, target=_TARGET_ARRAY_BUFFER)
    weights1_accessor = builder.add_vec_float(weights_1, 4, target=_TARGET_ARRAY_BUFFER)
    indices_accessor = builder.add_indices_uint16(faces.reshape(-1))

    inverse_bind_accessor = builder.add_mat4_float(
        np.linalg.inv(bind_global)
    )

    time_accessor = builder.add_scalar_float(
        np.arange(animation_motion.NumFrames, dtype=np.float32) / float(animation_motion.Framerate)
    )

    nodes: list[Node] = []
    children_of: list[list[int]] = [[] for _ in export_node_names]
    root_nodes: list[int] = []
    for node_index, parent_index in enumerate(export_parent_indices):
        if parent_index < 0:
            root_nodes.append(node_index)
        else:
            children_of[parent_index].append(node_index)

    for node_index, node_name in enumerate(export_node_names):
        node = Node(
            name=node_name,
            translation=bind_local_positions[node_index].astype(float).tolist(),
            rotation=bind_local_rotations[node_index].astype(float).tolist(),
            children=children_of[node_index] if children_of[node_index] else [],
        )
        nodes.append(node)

    mesh_node_index = len(nodes)
    nodes.append(
        Node(
            name="SOMA_HUMAN_BODY_Mesh",
            mesh=0,
            skin=0,
        )
    )

    attributes = Attributes(POSITION=position_accessor, NORMAL=normal_accessor)
    setattr(attributes, "JOINTS_0", joints0_accessor)
    setattr(attributes, "JOINTS_1", joints1_accessor)
    setattr(attributes, "WEIGHTS_0", weights0_accessor)
    setattr(attributes, "WEIGHTS_1", weights1_accessor)

    mesh = Mesh(
        name="SOMA_HUMAN_BODY",
        primitives=[
            Primitive(
                attributes=attributes,
                indices=indices_accessor,
                mode=4,
            )
        ],
    )

    animation_samplers: list[AnimationSampler] = []
    animation_channels: list[AnimationChannel] = []
    for node_index, node_name in enumerate(export_node_names):
        translation_accessor = builder.add_vec_float(corrected_positions[:, node_index], 3)
        rotation_accessor = builder.add_vec_float(corrected_rotations[:, node_index], 4)

        translation_sampler_index = len(animation_samplers)
        animation_samplers.append(
            AnimationSampler(
                input=time_accessor,
                output=translation_accessor,
                interpolation="LINEAR",
            )
        )
        animation_channels.append(
            AnimationChannel(
                sampler=translation_sampler_index,
                target=AnimationChannelTarget(node=node_index, path="translation"),
            )
        )

        rotation_sampler_index = len(animation_samplers)
        animation_samplers.append(
            AnimationSampler(
                input=time_accessor,
                output=rotation_accessor,
                interpolation="LINEAR",
            )
        )
        animation_channels.append(
            AnimationChannel(
                sampler=rotation_sampler_index,
                target=AnimationChannelTarget(node=node_index, path="rotation"),
            )
        )

    gltf = GLTF2(
        asset=Asset(version="2.0", generator="ai4animationpy.SOMAInterop"),
        scene=0,
        scenes=[Scene(name="Scene", nodes=[mesh_node_index] + root_nodes)],
        nodes=nodes,
        meshes=[mesh],
        skins=[
            Skin(
                inverseBindMatrices=inverse_bind_accessor,
                joints=list(range(len(export_node_names))),
                skeleton=0,
                name="SOMA_HUMAN_BODY_Skin",
            )
        ],
        buffers=[Buffer(byteLength=len(builder.data))],
        bufferViews=builder.buffer_views,
        accessors=builder.accessors,
        animations=[
            Animation(
                name=animation_motion.Name,
                samplers=animation_samplers,
                channels=animation_channels,
            )
        ],
    )

    output_glb.parent.mkdir(parents=True, exist_ok=True)
    gltf.set_binary_blob(bytes(builder.data))
    gltf.save_binary(str(output_glb))

    motion_npz_path: str | None = None
    if output_motion_npz_path is not None:
        output_motion_npz = Path(output_motion_npz_path).resolve()
        output_motion_npz.parent.mkdir(parents=True, exist_ok=True)
        full_motion_for_npz = Motion.LoadFromBVH(
            str(
                Path(animation_bvh_path).resolve()
                if animation_bvh_path is not None
                else tpose_bvh
            ),
            scale=scale,
        )
        full_name_to_index = {
            name: index
            for index, name in enumerate(full_motion_for_npz.Hierarchy.BoneNames)
        }
        joint_indices = [full_name_to_index[name] for name in joint_names]
        joint_parent_names: list[str | None] = []
        for joint_name in joint_names:
            parent_name = full_motion_for_npz.Hierarchy.ParentNames[
                full_name_to_index[joint_name]
            ]
            joint_parent_names.append(parent_name if parent_name in joint_names else None)
        skinned_motion = Motion(
            name=full_motion_for_npz.Name,
            hierarchy=Hierarchy(joint_names, joint_parent_names),
            frames=np.asarray(full_motion_for_npz.GetBoneTransformations()[:, joint_indices], dtype=np.float32),
            framerate=full_motion_for_npz.Framerate,
        )
        skinned_motion.SaveToNPZ(str(output_motion_npz))
        motion_npz_path = str(output_motion_npz if output_motion_npz.suffix.lower() == ".npz" else output_motion_npz.with_suffix(".npz"))

    return SOMAExportResult(
        glb_path=str(output_glb),
        motion_npz_path=motion_npz_path,
    )
