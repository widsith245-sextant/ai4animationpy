"""Command-line entrypoints for engineering-oriented workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from ai4animation import Utility

from .Config import (
    ActorViewerConfig,
    MotionEditorConfig,
    ONNXExportConfig,
    SkeletonDefinition,
    UENNEBundleConfig,
)
from .Facade import EngineeringAPI


def _parse_shape(shape: str) -> tuple[int, ...]:
    values = tuple(int(item.strip()) for item in shape.split(",") if item.strip())
    if not values:
        raise ValueError("Shape must contain at least one integer.")
    return values


def _load_skeleton(args) -> SkeletonDefinition:
    module = Utility.LoadModule(args.definitions_path)
    return SkeletonDefinition.from_module(
        args.skeleton_name,
        module,
        bone_names_attr=args.bone_names_attr,
        contact_threshold=args.contact_threshold,
    )


def _add_definition_arguments(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--definitions-path",
        required=True,
        help="Absolute path to a Definitions.py file or another compatible skeleton file.",
    )
    parser.add_argument(
        "--skeleton-name",
        default="ProjectSkeleton",
        help="Stable skeleton identifier used in manifests and logs.",
    )
    parser.add_argument(
        "--bone-names-attr",
        default="FULL_BODY_NAMES",
        help="Variable name inside the definitions module that stores the skeleton bone list.",
    )
    parser.add_argument(
        "--contact-threshold",
        default=0.25,
        type=float,
        help="Velocity threshold used to seed default contact pair configs.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ai4a",
        description="Engineering facade for AI4AnimationPy quickstart and export workflows.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert = subparsers.add_parser("convert", help="Convert a motion directory to NPZ.")
    convert.add_argument("input_directory")
    convert.add_argument("--output-directory")
    convert.add_argument("--scale", default=1.0, type=float)
    _add_definition_arguments(convert)

    inspect_motion = subparsers.add_parser(
        "inspect-motion",
        help="Print a JSON summary for one motion asset.",
    )
    inspect_motion.add_argument("path")
    inspect_motion.add_argument("--scale", default=1.0, type=float)
    inspect_motion.add_argument("--definitions-path")
    inspect_motion.add_argument("--bone-names-attr", default="FULL_BODY_NAMES")
    inspect_motion.add_argument("--skeleton-name", default="ProjectSkeleton")
    inspect_motion.add_argument("--contact-threshold", default=0.25, type=float)

    dataset_summary = subparsers.add_parser(
        "dataset-summary",
        help="Write a JSON summary for an NPZ dataset directory.",
    )
    dataset_summary.add_argument("dataset_directory")
    dataset_summary.add_argument("output_path")
    dataset_summary.add_argument("--include-motion-details", action="store_true")
    dataset_summary.add_argument("--limit", default=5, type=int)

    actor = subparsers.add_parser("actor", help="Launch the engineering actor viewer.")
    actor.add_argument("model_path")
    actor.add_argument("--mode", default="standalone")
    actor.add_argument("--rotation-speed", default=120.0, type=float)
    _add_definition_arguments(actor)

    editor = subparsers.add_parser(
        "editor",
        help="Launch the engineering motion editor.",
    )
    editor.add_argument("dataset_directory")
    editor.add_argument("model_path")
    editor.add_argument("--mode", default="standalone")
    editor.add_argument("--max-files", type=int)
    editor.add_argument("--disable-guidance", action="store_true")
    editor.add_argument("--disable-mirror", action="store_true")
    editor.add_argument("--disable-contacts", action="store_true")
    _add_definition_arguments(editor)

    export_onnx = subparsers.add_parser(
        "export-onnx",
        help="Export a torch checkpoint or module to ONNX.",
    )
    export_onnx.add_argument("checkpoint_path")
    export_onnx.add_argument("output_path")
    export_onnx.add_argument(
        "--shape",
        help="Sample input shape, for example 1,324. If omitted, checkpoint.input_dim() is used when available.",
    )
    export_onnx.add_argument("--input-name", default="input")
    export_onnx.add_argument("--output-name", default="output")
    export_onnx.add_argument("--opset", default=17, type=int)
    export_onnx.add_argument("--metadata-path")

    ue_manifest = subparsers.add_parser(
        "ue-manifest",
        help="Write a UE/NNE bridge manifest for an exported ONNX model.",
    )
    ue_manifest.add_argument("onnx_path")
    ue_manifest.add_argument("manifest_path")
    ue_manifest.add_argument("--package-name", default="ai4animation-nne")
    ue_manifest.add_argument("--dataset-directory")
    ue_manifest.add_argument("--source-checkpoint")
    ue_manifest.add_argument("--sample-rate", type=int)
    ue_manifest.add_argument("--metadata-path")
    ue_manifest.add_argument("--runtime-name", default="NNERuntimeORTCpu")
    ue_manifest.add_argument("--primary-ue-skeleton", default="UE5 Manny/Quinn")
    ue_manifest.add_argument("--disable-custom-skeletons", action="store_true")
    ue_manifest.add_argument(
        "--extra-json",
        help="Optional path to a JSON file whose object should be merged into extra_metadata.",
    )
    _add_definition_arguments(ue_manifest)

    export_ue_clip = subparsers.add_parser(
        "export-ue-clip",
        help="Export one source motion into a Manny-oriented UE JSON import payload.",
    )
    export_ue_clip.add_argument("motion_path")
    export_ue_clip.add_argument("output_path")
    export_ue_clip.add_argument("--scale", default=1.0, type=float)
    export_ue_clip.add_argument("--root-translation-scale", default=1.0, type=float)
    export_ue_clip.add_argument("--definitions-path")
    export_ue_clip.add_argument("--bone-names-attr", default="FULL_BODY_NAMES")
    export_ue_clip.add_argument("--skeleton-name", default="ProjectSkeleton")
    export_ue_clip.add_argument("--contact-threshold", default=0.25, type=float)

    export_soma_glb = subparsers.add_parser(
        "export-soma-glb",
        help="Export SOMA_HUMAN_BODY skin + animation into a skinned GLB for UE import.",
    )
    export_soma_glb.add_argument("skin_npz_path")
    export_soma_glb.add_argument("tpose_bvh_path")
    export_soma_glb.add_argument("output_glb_path")
    export_soma_glb.add_argument("--animation-bvh-path")
    export_soma_glb.add_argument("--output-motion-npz-path")
    export_soma_glb.add_argument("--scale", default=0.01, type=float)

    export_soma_ue_json = subparsers.add_parser(
        "export-soma-ue-json",
        help="Export raw SOMA test animation NPZ into a UE direct-import JSON payload.",
    )
    export_soma_ue_json.add_argument("test_animation_npz_path")
    export_soma_ue_json.add_argument("skin_npz_path")
    export_soma_ue_json.add_argument("output_path")
    export_soma_ue_json.add_argument("--skeleton-asset", required=True)
    export_soma_ue_json.add_argument("--preview-mesh-asset", required=True)
    export_soma_ue_json.add_argument("--root-source-bone", default="Hips")
    export_soma_ue_json.add_argument("--rebase-root-translation-to-first-frame", action="store_true")
    export_soma_ue_json.add_argument("--root-translation-scale", default=1.0, type=float)

    args = parser.parse_args(argv)

    if args.command == "convert":
        skeleton = _load_skeleton(args)
        outputs = EngineeringAPI.convert_directory(
            args.input_directory,
            output_directory=args.output_directory,
            skeleton=skeleton,
            scale=args.scale,
        )
        print(json.dumps({"output_paths": outputs}, indent=2))
        return 0

    if args.command == "inspect-motion":
        skeleton = None
        if args.definitions_path:
            skeleton = _load_skeleton(args)
        summary = EngineeringAPI.inspect_motion(
            args.path,
            bone_names=None if skeleton is None else list(skeleton.bone_names),
            scale=args.scale,
        )
        print(json.dumps(summary, indent=2))
        return 0

    if args.command == "dataset-summary":
        path = EngineeringAPI.write_dataset_summary(
            args.dataset_directory,
            args.output_path,
            include_motion_details=args.include_motion_details,
            limit=args.limit,
        )
        print(path)
        return 0

    if args.command == "actor":
        skeleton = _load_skeleton(args)
        config = ActorViewerConfig(
            model_path=args.model_path,
            skeleton=skeleton,
            auto_rotate_degrees_per_second=args.rotation_speed,
        )
        EngineeringAPI.run_actor_viewer(config, mode=args.mode)
        return 0

    if args.command == "editor":
        skeleton = _load_skeleton(args)
        config = MotionEditorConfig(
            dataset_directory=args.dataset_directory,
            model_path=args.model_path,
            skeleton=skeleton,
            include_contacts=not args.disable_contacts,
            include_guidance=not args.disable_guidance,
            include_mirror=not args.disable_mirror,
            max_files=args.max_files,
        )
        EngineeringAPI.run_motion_editor(config, mode=args.mode)
        return 0

    if args.command == "export-onnx":
        checkpoint = torch.load(args.checkpoint_path, weights_only=False, map_location="cpu")
        if not isinstance(checkpoint, torch.nn.Module):
            raise TypeError(
                "The checkpoint must deserialize to a torch.nn.Module for export."
            )

        if args.shape is not None:
            input_shape = _parse_shape(args.shape)
        elif hasattr(checkpoint, "input_dim"):
            input_shape = (1, int(checkpoint.input_dim()))
        else:
            raise ValueError(
                "Provide --shape when the checkpoint does not expose input_dim()."
            )

        sample_input = torch.randn(*input_shape, dtype=torch.float32)
        path = EngineeringAPI.export_model_to_onnx(
            checkpoint,
            sample_input,
            ONNXExportConfig(
                output_path=args.output_path,
                input_name=args.input_name,
                output_name=args.output_name,
                opset_version=args.opset,
                metadata_path=args.metadata_path,
            ),
        )
        print(path)
        return 0

    if args.command == "ue-manifest":
        skeleton = _load_skeleton(args)
        extra_metadata = {}
        if args.extra_json:
            extra_metadata = json.loads(
                Path(args.extra_json).read_text(encoding="utf-8")
            )

        path = EngineeringAPI.write_ue_nne_bundle(
            UENNEBundleConfig(
                package_name=args.package_name,
                onnx_path=args.onnx_path,
                manifest_path=args.manifest_path,
                skeleton=skeleton,
                source_checkpoint=args.source_checkpoint,
                dataset_directory=args.dataset_directory,
                sample_rate=args.sample_rate,
                metadata_path=args.metadata_path,
                runtime_name=args.runtime_name,
                primary_ue_skeleton=args.primary_ue_skeleton,
                supports_custom_skeletons=not args.disable_custom_skeletons,
                extra_metadata=extra_metadata,
            )
        )
        print(path)
        return 0

    if args.command == "export-ue-clip":
        skeleton = None
        if args.definitions_path:
            skeleton = _load_skeleton(args)
        path = EngineeringAPI.export_motion_to_ue_manny_json(
            args.motion_path,
            args.output_path,
            bone_names=None if skeleton is None else list(skeleton.bone_names),
            scale=args.scale,
            root_translation_scale=args.root_translation_scale,
        )
        print(path)
        return 0

    if args.command == "export-soma-glb":
        result = EngineeringAPI.export_soma_skinned_glb(
            skin_npz_path=args.skin_npz_path,
            tpose_bvh_path=args.tpose_bvh_path,
            output_glb_path=args.output_glb_path,
            animation_bvh_path=args.animation_bvh_path,
            output_motion_npz_path=args.output_motion_npz_path,
            scale=args.scale,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "export-soma-ue-json":
        path = EngineeringAPI.export_soma_test_animation_to_ue_json(
            test_animation_npz_path=args.test_animation_npz_path,
            skin_npz_path=args.skin_npz_path,
            output_path=args.output_path,
            skeleton_asset=args.skeleton_asset,
            preview_mesh_asset=args.preview_mesh_asset,
            root_source_bone=args.root_source_bone,
            rebase_root_translation_to_first_frame=args.rebase_root_translation_to_first_frame,
            root_translation_scale=args.root_translation_scale,
        )
        print(path)
        return 0

    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
