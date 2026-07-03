from pathlib import Path

import numpy as np

from ai4animation import AI4Animation
from ai4animation.Engineering import EngineeringAPI, MotionEditorConfig, SkeletonDefinition


REPO_ROOT = Path(__file__).resolve().parents[2]
SOMA_DIR = REPO_ROOT / "Artifacts" / "UE" / "SOMA"
SOURCE_DIR = REPO_ROOT / "skeletons" / "somaskel77"
TEST_BVH = REPO_ROOT / "Test_Animation" / "output1.bvh"
SKIN_NPZ = SOURCE_DIR / "skin_standard.npz"
TPOSE_BVH = SOURCE_DIR / "somaskel77_standard_tpose.bvh"
MODEL_GLB = SOMA_DIR / "SOMA_TestAnimation_Output1.glb"
DATASET_NPZ = SOMA_DIR / "output1_source.npz"


def _ensure_exported_assets() -> None:
    if MODEL_GLB.exists() and DATASET_NPZ.exists():
        return

    EngineeringAPI.export_soma_skinned_glb(
        skin_npz_path=str(SKIN_NPZ),
        tpose_bvh_path=str(TPOSE_BVH),
        output_glb_path=str(MODEL_GLB),
        animation_bvh_path=str(TEST_BVH),
        output_motion_npz_path=str(SOMA_DIR / "output1_source"),
        scale=0.01,
    )


def _load_skeleton() -> SkeletonDefinition:
    with np.load(SKIN_NPZ, allow_pickle=True) as data:
        bone_names = tuple(str(name) for name in data["rig_joint_names"].tolist())
    return SkeletonDefinition(
        name="SOMA_HUMAN_BODY",
        bone_names=bone_names,
        hip_name="Hips",
        left_hip_name="LeftLeg",
        right_hip_name="RightLeg",
        left_shoulder_name="LeftShoulder",
        right_shoulder_name="RightShoulder",
        neck_name="Neck1",
        contact_pairs=(
            ("LeftFoot", 0.25),
            ("LeftToeBase", 0.25),
            ("RightFoot", 0.25),
            ("RightToeBase", 0.25),
        ),
    )


def main() -> None:
    _ensure_exported_assets()
    config = MotionEditorConfig(
        dataset_directory=str(SOMA_DIR),
        model_path=str(MODEL_GLB),
        skeleton=_load_skeleton(),
        max_files=1,
    )
    EngineeringAPI.run_motion_editor(config, mode=AI4Animation.Mode.STANDALONE)


if __name__ == "__main__":
    main()
