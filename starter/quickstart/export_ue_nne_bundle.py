from pathlib import Path

import torch

from ai4animation import Utility
from ai4animation.Engineering import (
    EngineeringAPI,
    ONNXExportConfig,
    SkeletonDefinition,
    UENNEBundleConfig,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_PATH = REPO_ROOT / "Demos" / "_ASSETS_" / "Geno"
DEFINITIONS = Utility.LoadModule(str(ASSETS_PATH / "Definitions.py"))
SKELETON = SkeletonDefinition.from_module("Geno", DEFINITIONS)
CHECKPOINT_PATH = REPO_ROOT / "Demos" / "Locomotion" / "Biped" / "Network.pt"
PACKAGE_NAME = "geno-biped-locomotion"
ARTIFACTS_PATH = REPO_ROOT / "Artifacts" / "UE" / PACKAGE_NAME


def main():
    model = torch.load(CHECKPOINT_PATH, weights_only=False, map_location="cpu")
    sample_input = torch.randn(1, int(model.input_dim()), dtype=torch.float32)

    onnx_path = EngineeringAPI.export_model_to_onnx(
        model,
        sample_input,
        ONNXExportConfig(
            output_path=str(ARTIFACTS_PATH / f"{PACKAGE_NAME}.onnx"),
            metadata_path=str(ARTIFACTS_PATH / f"{PACKAGE_NAME}.metadata.json"),
        ),
    )

    manifest_path = EngineeringAPI.write_ue_nne_bundle(
        UENNEBundleConfig(
            package_name=PACKAGE_NAME,
            onnx_path=f"{PACKAGE_NAME}.onnx",
            manifest_path=str(ARTIFACTS_PATH / f"{PACKAGE_NAME}.ue.json"),
            skeleton=SKELETON,
            source_checkpoint=str(CHECKPOINT_PATH),
            dataset_directory=str(ASSETS_PATH / "Motions"),
            sample_rate=30,
            metadata_path=str(ARTIFACTS_PATH / f"{PACKAGE_NAME}.metadata.json"),
            preserve_relative_paths=True,
        )
    )

    print(onnx_path)
    print(manifest_path)


if __name__ == "__main__":
    main()
