import json
import os
import re
from pathlib import Path

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


def _resolve_asset_name(payload: dict, json_path: Path) -> str:
    clip_name = str(payload.get("clip_name", "")).strip() or json_path.stem
    return f"SOMA_{_safe_asset_name(clip_name)}_Anim"


def _import_one(
    *,
    json_path: Path,
    destination_path: str,
    skeleton_path: str,
    preview_mesh_path: str,
) -> str:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    asset_name = _resolve_asset_name(payload, json_path)
    target_asset_path = f"{destination_path.rstrip('/')}/{asset_name}"

    if unreal.EditorAssetLibrary.does_asset_exist(target_asset_path):
        unreal.log_warning(f"[AI4AnimationPy] Replacing existing asset: {target_asset_path}")
        unreal.EditorAssetLibrary.delete_asset(target_asset_path)

    result = unreal.AI4AnimationNNEEditorLibrary.import_clip_from_json(
        str(json_path),
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
        raise RuntimeError(error_message or f"ImportClipFromJson returned false for {json_path}.")

    if not asset_path:
        asset_path = target_asset_path

    if not unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False):
        raise RuntimeError(f"Imported asset was created but could not be saved: {asset_path}")

    unreal.log(f"[AI4AnimationPy] Imported SOMA animation asset: {asset_path}")
    return asset_path


def main() -> None:
    json_dir = Path(_required_env("AI4A_IMPORT_JSON_DIR")).resolve()
    destination_path = os.environ.get("AI4A_IMPORT_DEST", "/Game/AI4Animation/SOMA").strip()
    skeleton_path = os.environ.get(
        "AI4A_IMPORT_SKELETON",
        "/Game/AI4Animation/SOMA/SOMA_TestAnimation_Output1_Skeleton.SOMA_TestAnimation_Output1_Skeleton",
    ).strip()
    preview_mesh_path = os.environ.get(
        "AI4A_IMPORT_PREVIEW_MESH",
        "/Game/AI4Animation/SOMA/SOMA_TestAnimation_Output1.SOMA_TestAnimation_Output1",
    ).strip()

    if not json_dir.exists():
        raise RuntimeError(f"SOMA import JSON directory not found: {json_dir}")

    json_paths = sorted(json_dir.glob("*.json"))
    if not json_paths:
        raise RuntimeError(f"No SOMA import JSON files found in: {json_dir}")

    imported = []
    for json_path in json_paths:
        imported.append(
            _import_one(
                json_path=json_path,
                destination_path=destination_path,
                skeleton_path=skeleton_path,
                preview_mesh_path=preview_mesh_path,
            )
        )

    unreal.log(f"[AI4AnimationPy] Imported {len(imported)} SOMA animation assets from {json_dir}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - executes inside UE Python
        unreal.log_error(f"[AI4AnimationPy] {exc}")
        raise
