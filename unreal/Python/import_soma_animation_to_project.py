import os
import json
import re

import unreal


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _safe_asset_name(value: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z_]+", "_", value.strip())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "SOMA_Clip"


def main() -> None:
    json_path = _required_env("AI4A_IMPORT_JSON")
    destination_path = os.environ.get("AI4A_IMPORT_DEST", "/Game/AI4Animation/SOMA").strip()
    asset_name = os.environ.get("AI4A_IMPORT_ASSET", "").strip()
    skeleton_path = os.environ.get(
        "AI4A_IMPORT_SKELETON",
        "/Game/AI4Animation/SOMA/SOMA_TestAnimation_Output1_Skeleton.SOMA_TestAnimation_Output1_Skeleton",
    ).strip()
    preview_mesh_path = os.environ.get(
        "AI4A_IMPORT_PREVIEW_MESH",
        "/Game/AI4Animation/SOMA/SOMA_TestAnimation_Output1.SOMA_TestAnimation_Output1",
    ).strip()

    if not asset_name:
        with open(json_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        clip_name = str(payload.get("clip_name", "")).strip()
        asset_name = f"SOMA_{_safe_asset_name(clip_name)}_Anim"

    target_asset_path = f"{destination_path.rstrip('/')}/{asset_name}"

    if unreal.EditorAssetLibrary.does_asset_exist(target_asset_path):
        unreal.log_warning(f"[AI4AnimationPy] Replacing existing asset: {target_asset_path}")
        unreal.EditorAssetLibrary.delete_asset(target_asset_path)

    result = unreal.AI4AnimationNNEEditorLibrary.import_clip_from_json(
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
            raise RuntimeError(f"Unexpected return value from import_clip_from_json: {result!r}")
    else:
        success = bool(result)

    if not success:
        raise RuntimeError(error_message or "ImportClipFromJson returned false.")

    if not asset_path:
        asset_path = target_asset_path

    if not unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False):
        raise RuntimeError(f"Imported asset was created but could not be saved: {asset_path}")

    unreal.log(f"[AI4AnimationPy] Imported SOMA animation asset: {asset_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - executes inside UE Python
        unreal.log_error(f"[AI4AnimationPy] {exc}")
        raise
