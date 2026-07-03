import os
import shutil
from pathlib import Path

import unreal


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _list_assets(destination_path: str) -> list[str]:
    asset_paths = unreal.EditorAssetLibrary.list_assets(
        destination_path,
        recursive=True,
        include_folder=False,
    )
    return sorted(asset_paths)


def _game_path_to_content_dir(destination_path: str) -> Path:
    if not destination_path.startswith("/Game"):
        raise RuntimeError(f"Unsupported destination path: {destination_path}")
    relative = destination_path[len("/Game"):].strip("/").replace("/", os.sep)
    return Path(unreal.Paths.project_content_dir()) / relative


def _clear_destination_assets(destination_path: str) -> None:
    # Try UE-side deletion first so the asset registry drops references cleanly.
    if unreal.EditorAssetLibrary.does_directory_exist(destination_path):
        for asset_path in reversed(_list_assets(destination_path)):
            try:
                unreal.EditorAssetLibrary.delete_asset(asset_path)
            except Exception as exc:
                unreal.log_warning(
                    f"[AI4AnimationPy] UE asset delete failed for {asset_path}: {exc}"
                )

    # Then hard-reset the on-disk content folder so re-import is guaranteed fresh.
    destination_dir = _game_path_to_content_dir(destination_path)
    if destination_dir.exists():
        shutil.rmtree(destination_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    unreal.log(f"[AI4AnimationPy] Cleared destination directory {destination_dir}")


def main() -> None:
    source_glb = _required_env("AI4A_SOMA_SOURCE_GLB")
    destination_path = os.environ.get("AI4A_SOMA_IMPORT_DEST", "/Game/AI4Animation/SOMA").strip()
    clear_destination = os.environ.get("AI4A_SOMA_CLEAR_DEST", "0").strip() == "1"

    if clear_destination:
        _clear_destination_assets(destination_path)

    task = unreal.AssetImportTask()
    task.filename = source_glb
    task.destination_path = destination_path
    task.automated = True
    task.replace_existing = True
    task.replace_existing_settings = True
    task.save = True

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    imported_paths = list(task.imported_object_paths)
    if not imported_paths:
        imported_paths = _list_assets(destination_path)

    if not imported_paths:
        raise RuntimeError(
            f"No assets were imported from {source_glb} into {destination_path}."
        )

    unreal.log(f"[AI4AnimationPy] Imported SOMA source assets into {destination_path}")
    for asset_path in imported_paths:
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        class_name = asset.get_class().get_name() if asset else "Unknown"
        unreal.log(f"[AI4AnimationPy] imported_asset={asset_path} class={class_name}")
        unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - executes inside UE Python
        unreal.log_error(f"[AI4AnimationPy] {exc}")
        raise
