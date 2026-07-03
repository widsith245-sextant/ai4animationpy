import os
import sys

import unreal


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    json_path = _required_env("AI4A_IMPORT_JSON")
    destination_path = os.environ.get("AI4A_IMPORT_DEST", "/Game/AI4Animation/TestAnimations").strip()
    asset_name = os.environ.get("AI4A_IMPORT_ASSET", "AN_TestAnimation_Output1_Manny").strip()
    skeleton_path = os.environ.get(
        "AI4A_IMPORT_SKELETON",
        "/Game/Characters/Mannequins/Meshes/SK_Mannequin.SK_Mannequin",
    ).strip()
    preview_mesh_path = os.environ.get(
        "AI4A_IMPORT_PREVIEW_MESH",
        "/Game/Characters/Mannequins/Meshes/SKM_Manny.SKM_Manny",
    ).strip()
    target_asset_path = f"{destination_path.rstrip('/')}/{asset_name}"

    if unreal.EditorAssetLibrary.does_asset_exist(target_asset_path):
        unreal.log_warning(f"[AI4AnimationPy] Replacing existing asset: {target_asset_path}")
        unreal.EditorAssetLibrary.delete_asset(target_asset_path)

    result = unreal.AI4AnimationNNEEditorLibrary.import_manny_clip_from_json(
        json_path,
        destination_path,
        asset_name,
        skeleton_path,
        preview_mesh_path,
    )

    success = False
    asset_path = ""
    error_message = ""
    if isinstance(result, tuple):
        if len(result) == 3:
            success, asset_path, error_message = result
        elif len(result) == 2:
            success, asset_path = result
        elif len(result) == 1:
            success = bool(result[0])
        else:
            raise RuntimeError(f"Unexpected return value from import_manny_clip_from_json: {result!r}")
    else:
        success = bool(result)

    if not success:
        raise RuntimeError(error_message or "ImportMannyClipFromJson returned false.")

    if not asset_path:
        asset_path = target_asset_path

    if not unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False):
        raise RuntimeError(f"Imported asset was created but could not be saved: {asset_path}")

    unreal.log(f"[AI4AnimationPy] Imported Manny animation asset: {asset_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - executes inside UE Python
        unreal.log_error(f"[AI4AnimationPy] {exc}")
        raise
