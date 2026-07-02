from pathlib import Path

from ai4animation import AI4Animation, Utility
from ai4animation.Engineering import ActorViewerConfig, EngineeringAPI, SkeletonDefinition

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_PATH = REPO_ROOT / "Demos" / "_ASSETS_" / "Cranberry"
DEFINITIONS = Utility.LoadModule(str(ASSETS_PATH / "Definitions.py"))
SKELETON = SkeletonDefinition.from_module("Cranberry", DEFINITIONS)


def main():
    config = ActorViewerConfig(
        model_path=str(ASSETS_PATH / "Model.glb"),
        skeleton=SKELETON,
    )
    EngineeringAPI.run_actor_viewer(config, mode=AI4Animation.Mode.STANDALONE)


if __name__ == "__main__":
    main()
