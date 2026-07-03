"""Engineering-oriented facade for app startup, conversion, and UE export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch

from ai4animation.AI4Animation import AI4Animation
from ai4animation.Animation.Dataset import Dataset
from ai4animation.Animation.Motion import Motion
from ai4animation.Import.BatchConverter import Run as RunBatchConverter

from .Config import (
    ActorViewerConfig,
    MotionEditorConfig,
    ONNXExportConfig,
    SkeletonDefinition,
    UENNEBundleConfig,
)
from .Programs import ActorViewerProgram, EmptyProgram, MotionEditorProgram
from .SOMAInterop import export_skinned_soma_glb
from .UEInterop import export_motion_for_ue_manny, export_soma_test_animation_npz_for_ue


class EngineeringAPI:
    """High-level facade meant for application integration rather than experiments."""

    @staticmethod
    def _normalize_mode(mode: str | AI4Animation.Mode | None):
        if mode is None:
            return None
        if isinstance(mode, AI4Animation.Mode):
            return mode
        return AI4Animation.Mode[str(mode).upper()]

    @staticmethod
    def load_motion(
        path: str,
        bone_names: list[str] | tuple[str, ...] | None = None,
        scale: float = 1.0,
        operation=None,
    ) -> Motion:
        suffix = Path(path).suffix.lower()
        if suffix == ".npz":
            return Motion.LoadFromNPZ(path, operation=operation)
        if suffix == ".glb":
            return Motion.LoadFromGLB(path, names=bone_names, operation=operation)
        if suffix == ".fbx":
            return Motion.LoadFromFBX(path, names=bone_names, operation=operation)
        if suffix == ".bvh":
            return Motion.LoadFromBVH(
                path,
                names=bone_names,
                scale=scale,
                operation=operation,
            )
        raise ValueError(f"Unsupported motion format: {path}")

    @staticmethod
    def inspect_motion(
        path: str,
        bone_names: list[str] | tuple[str, ...] | None = None,
        scale: float = 1.0,
    ) -> dict[str, Any]:
        motion = EngineeringAPI.load_motion(path, bone_names=bone_names, scale=scale)
        return {
            "name": motion.Name,
            "path": str(Path(path).resolve()),
            "num_frames": int(motion.NumFrames),
            "num_joints": int(motion.NumJoints),
            "framerate": float(motion.Framerate),
            "duration_seconds": float(motion.TotalTime),
            "bone_names": list(motion.Hierarchy.BoneNames),
            "parent_names": list(motion.Hierarchy.ParentNames),
        }

    @staticmethod
    def convert_directory(
        input_directory: str,
        output_directory: str | None = None,
        skeleton: SkeletonDefinition | None = None,
        scale: float = 1.0,
    ) -> list[str]:
        bone_names = None if skeleton is None else list(skeleton.bone_names)
        return RunBatchConverter(
            input_directory,
            output_directory,
            bone_names=bone_names,
            scale=scale,
        )

    @staticmethod
    def build_dataset(config: MotionEditorConfig) -> Dataset:
        return Dataset(
            config.dataset_directory,
            config.create_modules(),
            max_files=config.max_files,
        )

    @staticmethod
    def summarize_dataset(
        dataset_directory: str,
        include_motion_details: bool = False,
        limit: int = 5,
    ) -> dict[str, Any]:
        dataset_path = Path(dataset_directory).resolve()
        files = sorted(dataset_path.rglob("*.npz"))
        summary = {
            "directory": str(dataset_path),
            "count": len(files),
            "sample_files": [str(path) for path in files[:limit]],
        }

        if include_motion_details:
            summary["motions"] = [
                EngineeringAPI.inspect_motion(str(path))
                for path in files[:limit]
            ]

        return summary

    @staticmethod
    def write_dataset_summary(
        dataset_directory: str,
        output_path: str,
        include_motion_details: bool = False,
        limit: int = 5,
    ) -> str:
        summary = EngineeringAPI.summarize_dataset(
            dataset_directory,
            include_motion_details=include_motion_details,
            limit=limit,
        )
        output = Path(output_path).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        return str(output)

    @staticmethod
    def run_empty(mode: str | AI4Animation.Mode | None = None):
        return AI4Animation(EmptyProgram(), mode=EngineeringAPI._normalize_mode(mode))

    @staticmethod
    def run_actor_viewer(
        config: ActorViewerConfig,
        mode: str | AI4Animation.Mode | None = None,
    ):
        return AI4Animation(
            ActorViewerProgram(config),
            mode=EngineeringAPI._normalize_mode(mode),
        )

    @staticmethod
    def run_motion_editor(
        config: MotionEditorConfig,
        mode: str | AI4Animation.Mode | None = None,
    ):
        return AI4Animation(
            MotionEditorProgram(config),
            mode=EngineeringAPI._normalize_mode(mode),
        )

    @staticmethod
    def export_model_to_onnx(
        model: torch.nn.Module,
        sample_input: torch.Tensor,
        config: ONNXExportConfig,
    ) -> str:
        output_path = Path(config.output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        dynamic_axes = None
        if config.dynamic_batch:
            dynamic_axes = {
                config.input_name: {0: "batch"},
                config.output_name: {0: "batch"},
            }

        model.eval()
        with torch.no_grad():
            try:
                torch.onnx.export(
                    model,
                    sample_input,
                    str(output_path),
                    export_params=True,
                    do_constant_folding=True,
                    opset_version=config.opset_version,
                    input_names=[config.input_name],
                    output_names=[config.output_name],
                    dynamic_axes=dynamic_axes,
                    dynamo=False,
                )
            except Exception as exc:
                raise RuntimeError(
                    "ONNX export failed. Install the ONNX tooling if it is missing "
                    "and verify the checkpoint can run a forward pass with the "
                    "provided sample input."
                ) from exc

        metadata = {
            "output_path": str(output_path),
            "input_name": config.input_name,
            "output_name": config.output_name,
            "input_shape": list(sample_input.shape),
            "opset_version": config.opset_version,
            "dynamic_batch": config.dynamic_batch,
        }

        if config.metadata_path is not None:
            metadata_path = Path(config.metadata_path).resolve()
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        return str(output_path)

    @staticmethod
    def write_ue_nne_bundle(config: UENNEBundleConfig) -> str:
        manifest_path = Path(config.manifest_path).resolve()
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        model_io = None
        if config.metadata_path is not None:
            metadata_path = Path(config.metadata_path).resolve()
            if metadata_path.exists():
                model_io = json.loads(metadata_path.read_text(encoding="utf-8"))

        onnx_path_value = (
            config.onnx_path
            if config.preserve_relative_paths
            else str(Path(config.onnx_path).resolve())
        )

        manifest: dict[str, Any] = {
            "schema_version": "1.0",
            "package_name": config.package_name,
            "runtime": {
                "preferred_name": config.runtime_name,
                "target": "UnrealEngine.NNE",
            },
            "onnx": {
                "path": onnx_path_value,
                "runtime_target": "UnrealEngine.NNE",
            },
            "skeleton": config.skeleton.to_metadata(),
            "retargeting": {
                "primary_ue_skeleton": config.primary_ue_skeleton,
                "supports_custom_skeletons": config.supports_custom_skeletons,
                "strategy": "UE IK Retargeter / native retarget pipeline",
            },
            "compatible_input_formats": list(config.compatible_input_formats),
            "terrain": {
                "supports_variable_slope": config.terrain_supports_slope,
                "supports_height_variation": config.terrain_supports_height_variation,
                "training_expectation": "Gym environments should include terrain randomization and slope changes.",
            },
            "bridge_contract": {
                "authoring_source": "AI4AnimationPy",
                "runtime_target": "UE + NNE",
                "preprocess_requirements": [
                    "Match FeedTensor feature ordering exactly.",
                    "Keep root-relative transforms consistent between Python and UE.",
                    "Export and replay normalization/statistics alongside the network.",
                    "Treat motion conversion outputs (.npz) as the training source of truth.",
                ],
            },
        }

        if model_io is not None:
            manifest["model_io"] = model_io

        if config.source_checkpoint is not None:
            manifest["source_checkpoint"] = (
                config.source_checkpoint
                if config.preserve_relative_paths
                else str(Path(config.source_checkpoint).resolve())
            )

        if config.dataset_directory is not None:
            manifest["dataset"] = EngineeringAPI.summarize_dataset(
                config.dataset_directory,
                include_motion_details=True,
                limit=5,
            )

        if config.sample_rate is not None:
            manifest["sample_rate"] = config.sample_rate

        if config.extra_metadata:
            manifest["extra_metadata"] = config.extra_metadata

        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return str(manifest_path)

    @staticmethod
    def export_motion_to_ue_manny_json(
        motion_path: str,
        output_path: str,
        *,
        bone_names: list[str] | tuple[str, ...] | None = None,
        scale: float = 1.0,
        root_translation_scale: float = 1.0,
    ) -> str:
        motion = EngineeringAPI.load_motion(
            motion_path,
            bone_names=bone_names,
            scale=scale,
        )
        return export_motion_for_ue_manny(
            motion,
            output_path,
            source_path=motion_path,
            root_translation_scale=root_translation_scale,
        )

    @staticmethod
    def export_soma_skinned_glb(
        *,
        skin_npz_path: str,
        tpose_bvh_path: str,
        output_glb_path: str,
        animation_bvh_path: str | None = None,
        output_motion_npz_path: str | None = None,
        scale: float = 0.01,
    ) -> dict[str, str | None]:
        result = export_skinned_soma_glb(
            skin_npz_path=skin_npz_path,
            tpose_bvh_path=tpose_bvh_path,
            output_glb_path=output_glb_path,
            animation_bvh_path=animation_bvh_path,
            output_motion_npz_path=output_motion_npz_path,
            scale=scale,
        )
        return {
            "glb_path": result.glb_path,
            "motion_npz_path": result.motion_npz_path,
        }

    @staticmethod
    def export_soma_test_animation_to_ue_json(
        *,
        test_animation_npz_path: str,
        skin_npz_path: str,
        output_path: str,
        skeleton_asset: str,
        preview_mesh_asset: str,
        root_source_bone: str = "Hips",
        rebase_root_translation_to_first_frame: bool = False,
        root_translation_scale: float = 1.0,
    ) -> str:
        return export_soma_test_animation_npz_for_ue(
            test_animation_npz_path=test_animation_npz_path,
            skin_npz_path=skin_npz_path,
            output_path=output_path,
            skeleton_asset=skeleton_asset,
            preview_mesh_asset=preview_mesh_asset,
            root_source_bone=root_source_bone,
            rebase_root_translation_to_first_frame=rebase_root_translation_to_first_frame,
            root_translation_scale=root_translation_scale,
        )
