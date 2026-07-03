"""UE-facing motion export helpers for project-level import automation."""

from __future__ import annotations

import json
from pathlib import Path
import numpy as np

from ai4animation.Animation.Motion import Motion
from ai4animation.Math import Quaternion, Transform


UE_MANNY_TEST_MAPPING: dict[str, str] = {
    "root": "Root",
    "pelvis": "Hips",
    "spine_01": "Spine1",
    "spine_02": "Spine2",
    "spine_03": "Chest",
    "neck_01": "Neck1",
    "neck_02": "Neck2",
    "head": "Head",
    "clavicle_l": "LeftShoulder",
    "upperarm_l": "LeftArm",
    "lowerarm_l": "LeftForeArm",
    "hand_l": "LeftHand",
    "thumb_01_l": "LeftHandThumb1",
    "thumb_02_l": "LeftHandThumb2",
    "thumb_03_l": "LeftHandThumb3",
    "index_01_l": "LeftHandIndex1",
    "index_02_l": "LeftHandIndex2",
    "index_03_l": "LeftHandIndex3",
    "middle_01_l": "LeftHandMiddle1",
    "middle_02_l": "LeftHandMiddle2",
    "middle_03_l": "LeftHandMiddle3",
    "ring_01_l": "LeftHandRing1",
    "ring_02_l": "LeftHandRing2",
    "ring_03_l": "LeftHandRing3",
    "pinky_01_l": "LeftHandPinky1",
    "pinky_02_l": "LeftHandPinky2",
    "pinky_03_l": "LeftHandPinky3",
    "clavicle_r": "RightShoulder",
    "upperarm_r": "RightArm",
    "lowerarm_r": "RightForeArm",
    "hand_r": "RightHand",
    "thumb_01_r": "RightHandThumb1",
    "thumb_02_r": "RightHandThumb2",
    "thumb_03_r": "RightHandThumb3",
    "index_01_r": "RightHandIndex1",
    "index_02_r": "RightHandIndex2",
    "index_03_r": "RightHandIndex3",
    "middle_01_r": "RightHandMiddle1",
    "middle_02_r": "RightHandMiddle2",
    "middle_03_r": "RightHandMiddle3",
    "ring_01_r": "RightHandRing1",
    "ring_02_r": "RightHandRing2",
    "ring_03_r": "RightHandRing3",
    "pinky_01_r": "RightHandPinky1",
    "pinky_02_r": "RightHandPinky2",
    "pinky_03_r": "RightHandPinky3",
    "thigh_l": "LeftLeg",
    "calf_l": "LeftShin",
    "foot_l": "LeftFoot",
    "ball_l": "LeftToeBase",
    "thigh_r": "RightLeg",
    "calf_r": "RightShin",
    "foot_r": "RightFoot",
    "ball_r": "RightToeBase",
}


def _convert_positions_to_unreal_cm(positions: np.ndarray) -> np.ndarray:
    """Convert AI4Animation world positions to the UE skeleton import basis.

    The Interchange glTF importer brings SOMA assets into UE with axes remapped
    from (x, y, z) to (x, z, y) and meters converted to centimeters.
    """

    positions = np.asarray(positions, dtype=np.float32)
    converted = np.empty_like(positions, dtype=np.float32)
    converted[..., 0] = positions[..., 0] * 100.0
    converted[..., 1] = positions[..., 2] * 100.0
    converted[..., 2] = positions[..., 1] * 100.0
    return converted


def _convert_quaternions_to_unreal_basis(quaternions: np.ndarray) -> np.ndarray:
    """Match UE's imported SOMA skeleton basis for quaternion animation keys."""

    quaternions = np.asarray(quaternions, dtype=np.float32)
    converted = np.empty_like(quaternions, dtype=np.float32)
    converted[..., 0] = -quaternions[..., 0]
    converted[..., 1] = -quaternions[..., 2]
    converted[..., 2] = -quaternions[..., 1]
    converted[..., 3] = quaternions[..., 3]
    return converted


def export_motion_for_ue_manny(
    motion: Motion,
    output_path: str,
    *,
    source_path: str | None = None,
    root_translation_scale: float = 1.0,
) -> str:
    """Export one motion clip into a Manny-oriented JSON bridge contract."""

    transforms = motion.GetBoneTransformations()
    world_positions = Transform.GetPosition(transforms)
    world_rotations = Quaternion.FromMatrix(Transform.GetRotation(transforms))

    bone_names = list(motion.Hierarchy.BoneNames)
    bone_indices = {name: index for index, name in enumerate(bone_names)}

    source_tracks: dict[str, dict[str, list[list[float]]]] = {}
    missing_sources: dict[str, str] = {}
    for target_bone, source_bone in UE_MANNY_TEST_MAPPING.items():
        source_index = bone_indices.get(source_bone)
        if source_index is None:
            missing_sources[target_bone] = source_bone
            continue

        source_tracks[source_bone] = {
            "positions": world_positions[:, source_index].tolist(),
            "rotations": world_rotations[:, source_index].tolist(),
        }

    root_source = UE_MANNY_TEST_MAPPING["root"]
    payload = {
        "schema_version": "1.0",
        "exporter": "ai4animationpy",
        "clip_name": motion.Name,
        "source_path": None if source_path is None else str(Path(source_path).resolve()),
        "frame_rate": float(motion.Framerate),
        "num_frames": int(motion.NumFrames),
        "source_bone_count": int(motion.NumJoints),
        "target_profile": {
            "name": "UE5 Manny",
            "skeleton_asset": "/Game/Characters/Mannequins/Meshes/SK_Mannequin",
            "preview_mesh_asset": "/Game/Characters/Mannequins/Meshes/SKM_Manny",
        },
        "options": {
            "root_source_bone": root_source,
            "rebase_root_translation_to_first_frame": True,
            "root_translation_scale": float(root_translation_scale),
        },
        "bone_mapping": UE_MANNY_TEST_MAPPING,
        "source_tracks": source_tracks,
        "missing_sources": missing_sources,
    }

    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(output)


def export_soma_test_animation_npz_for_ue(
    test_animation_npz_path: str,
    skin_npz_path: str,
    output_path: str,
    *,
    skeleton_asset: str,
    preview_mesh_asset: str,
    root_source_bone: str = "Hips",
    rebase_root_translation_to_first_frame: bool = False,
    root_translation_scale: float = 1.0,
) -> str:
    """Export raw SOMA test animation NPZ into a direct UE import payload.

    The payload preserves the SOMA bind offsets and drives the clip through
    source global joint rotations plus exact root/Hips motion. This matches the
    upstream Kimodo SOMA skinning path more closely than reconstructing from
    local_rot_mats alone, which can preserve joint positions while still
    drifting in bone-axis twist.
    """

    animation_data = np.load(Path(test_animation_npz_path).resolve(), allow_pickle=True)
    skin_data = np.load(Path(skin_npz_path).resolve(), allow_pickle=True)

    joint_names = [str(name) for name in skin_data["rig_joint_names"].tolist()]
    world_positions = _convert_positions_to_unreal_cm(
        np.asarray(animation_data["posed_joints"], dtype=np.float32)
    )
    world_rotations = _convert_quaternions_to_unreal_basis(
        np.asarray(
            Quaternion.FromMatrix(np.asarray(animation_data["global_rot_mats"], dtype=np.float32)),
            dtype=np.float32,
        )
    )

    if world_positions.shape[:2] != world_rotations.shape[:2]:
        raise ValueError(
            "posed_joints and global_rot_mats must share the same [frames, joints] dimensions."
        )
    if world_positions.shape[1] != len(joint_names):
        raise ValueError(
            f"Joint count mismatch: animation has {world_positions.shape[1]} joints, "
            f"skin defines {len(joint_names)} joints."
        )

    source_tracks = {
        joint_name: {
            "positions": world_positions[:, index].tolist(),
            "rotations": world_rotations[:, index].tolist(),
        }
        for index, joint_name in enumerate(joint_names)
    }

    payload = {
        "schema_version": "1.0",
        "exporter": "ai4animationpy",
        "clip_name": Path(test_animation_npz_path).stem,
        "source_path": str(Path(test_animation_npz_path).resolve()),
        "frame_rate": 30.0,
        "num_frames": int(world_positions.shape[0]),
        "source_bone_count": int(world_positions.shape[1]),
        "target_profile": {
            "name": "SOMA_HUMAN_BODY",
            "skeleton_asset": skeleton_asset,
            "preview_mesh_asset": preview_mesh_asset,
        },
        "options": {
            "root_source_bone": root_source_bone,
            "rebase_root_translation_to_first_frame": rebase_root_translation_to_first_frame,
            "root_translation_scale": float(root_translation_scale),
            "use_source_world_positions_for_all_bones": False,
            "source_rotations_are_local": False,
        },
        "bone_mapping": {joint_name: joint_name for joint_name in joint_names},
        "source_tracks": source_tracks,
        "missing_sources": {},
    }

    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(output)
