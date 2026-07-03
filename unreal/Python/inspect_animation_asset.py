import os

import unreal


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    asset_path = _required_env("AI4A_INSPECT_ASSET")
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not asset:
        raise RuntimeError(f"Failed to load asset: {asset_path}")

    unreal.log(f"[AI4AnimationPy] asset_class={asset.get_class().get_name()}")
    skeleton = None
    if hasattr(asset, "get_editor_property"):
        try:
            skeleton = asset.get_editor_property("skeleton")
        except Exception:
            skeleton = None
    if skeleton:
        unreal.log(f"[AI4AnimationPy] skeleton={skeleton.get_path_name()}")
    if hasattr(asset, "get_editor_property"):
        try:
            sequence_length = asset.get_editor_property("sequence_length")
            unreal.log(f"[AI4AnimationPy] sequence_length={sequence_length}")
        except Exception:
            pass
        try:
            num_frames = asset.get_number_of_frames()
            unreal.log(f"[AI4AnimationPy] num_frames={num_frames}")
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - executes inside UE Python
        unreal.log_error(f"[AI4AnimationPy] {exc}")
        raise
