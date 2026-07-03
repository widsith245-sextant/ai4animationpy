import os

import unreal


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _normalize_asset_path(asset_path: str) -> str:
    asset_path = asset_path.strip()
    if "." in asset_path:
        asset_path = asset_path.split(".", 1)[0]
    return asset_path


def _asset_name_from_path(asset_path: str) -> str:
    return asset_path.rsplit("/", 1)[-1]


def _delete_if_exists(asset_path: str) -> None:
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        unreal.EditorAssetLibrary.delete_asset(asset_path)


def _create_asset(asset_path: str, asset_class, factory):
    asset_path = _normalize_asset_path(asset_path)
    package_path = asset_path.rsplit("/", 1)[0]
    asset_name = _asset_name_from_path(asset_path)
    _delete_if_exists(asset_path)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name,
        package_path,
        asset_class,
        factory,
    )
    if not asset:
        raise RuntimeError(f"Failed to create asset: {asset_path}")
    return asset


def _load_asset(asset_path: str):
    asset = unreal.EditorAssetLibrary.load_asset(_normalize_asset_path(asset_path))
    if not asset:
        raise RuntimeError(f"Failed to load asset: {asset_path}")
    return asset


def _save_asset(asset_path: str) -> None:
    if not unreal.EditorAssetLibrary.save_asset(
        _normalize_asset_path(asset_path),
        only_if_is_dirty=False,
    ):
        raise RuntimeError(f"Failed to save asset: {asset_path}")


def _load_or_create_retargeter(
    *,
    source_mesh_path: str,
    source_ikrig_path: str,
    retargeter_path: str,
    target_mesh_path: str,
    target_ikrig_path: str,
):
    normalized_retargeter = _normalize_asset_path(retargeter_path)
    if unreal.EditorAssetLibrary.does_asset_exist(normalized_retargeter):
        retargeter = _load_asset(normalized_retargeter)
        unreal.log(f"[AI4AnimationPy] reusing_existing_retargeter={normalized_retargeter}")
        return retargeter

    if os.environ.get("AI4A_ALLOW_IKRIG_SETUP", "").strip() not in {"1", "true", "True", "yes"}:
        raise RuntimeError(
            "Retargeter asset not found and headless setup is disabled. "
            f"Create {normalized_retargeter} once in the editor, or set AI4A_ALLOW_IKRIG_SETUP=1."
        )

    source_mesh = _load_asset(source_mesh_path)
    target_mesh = _load_asset(target_mesh_path)
    target_ikrig = _load_asset(target_ikrig_path)

    source_ikrig = _create_asset(
        source_ikrig_path,
        unreal.IKRigDefinition,
        unreal.IKRigDefinitionFactory(),
    )
    source_ikrig_controller = unreal.IKRigController.get_controller(source_ikrig)
    if not source_ikrig_controller.set_skeletal_mesh(source_mesh):
        raise RuntimeError("Failed to assign SOMA source skeletal mesh to IKRig.")

    source_autogen_ok = source_ikrig_controller.apply_auto_generated_retarget_definition()
    unreal.log(f"[AI4AnimationPy] source_autogen_ok={source_autogen_ok}")
    _save_asset(source_ikrig_path)

    retargeter = _create_asset(
        retargeter_path,
        unreal.IKRetargeter,
        unreal.IKRetargetFactory(),
    )
    controller = unreal.IKRetargeterController.get_controller(retargeter)

    source_enum = unreal.RetargetSourceOrTarget.SOURCE
    target_enum = unreal.RetargetSourceOrTarget.TARGET

    controller.set_ik_rig(source_enum, source_ikrig)
    controller.set_preview_mesh(source_enum, source_mesh)
    controller.set_ik_rig(target_enum, target_ikrig)
    controller.set_preview_mesh(target_enum, target_mesh)
    controller.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
    controller.auto_align_all_bones(target_enum)
    _save_asset(retargeter_path)
    return retargeter


def main() -> None:
    source_mesh_path = _required_env("AI4A_SOMA_SOURCE_MESH")
    source_anim_path = _required_env("AI4A_SOMA_SOURCE_ANIM")
    source_ikrig_path = os.environ.get(
        "AI4A_SOMA_SOURCE_IKRIG",
        "/Game/AI4Animation/SOMA/IK_SOMA_TestAnimation_Output1",
    ).strip()
    retargeter_path = os.environ.get(
        "AI4A_SOMA_MANNY_RETARGETER",
        "/Game/AI4Animation/SOMA/RTG_SOMA_To_Manny",
    ).strip()
    target_anim_path = os.environ.get(
        "AI4A_SOMA_TARGET_ANIM",
        "/Game/AI4Animation/TestAnimations/AN_TestAnimation_Output1_SOMA_Manny",
    ).strip()

    target_mesh_path = os.environ.get(
        "AI4A_MANNY_TARGET_MESH",
        "/Game/Characters/Mannequins/Meshes/SKM_Manny",
    ).strip()
    target_ikrig_path = os.environ.get(
        "AI4A_MANNY_TARGET_IKRIG",
        "/Game/Characters/Mannequins/Rigs/IK_Mannequin",
    ).strip()

    source_mesh = _load_asset(source_mesh_path)
    _load_asset(source_anim_path)
    target_mesh = _load_asset(target_mesh_path)
    _load_asset(target_ikrig_path)

    retargeter = _load_or_create_retargeter(
        source_mesh_path=source_mesh_path,
        source_ikrig_path=source_ikrig_path,
        retargeter_path=retargeter_path,
        target_mesh_path=target_mesh_path,
        target_ikrig_path=target_ikrig_path,
    )

    target_anim_asset = _normalize_asset_path(target_anim_path)
    _delete_if_exists(target_anim_asset)

    source_anim_asset_data = unreal.EditorAssetLibrary.find_asset_data(
        _normalize_asset_path(source_anim_path)
    )
    if not source_anim_asset_data.is_valid():
        raise RuntimeError(f"Invalid source animation asset data: {source_anim_path}")

    retargeted_assets = unreal.IKRetargetBatchOperation.duplicate_and_retarget(
        [source_anim_asset_data],
        source_mesh,
        target_mesh,
        retargeter,
        "",
        "",
        "",
        "_Manny",
        True,
    )

    if not retargeted_assets:
        raise RuntimeError("DuplicateAndRetarget did not return any assets.")

    retargeted_anim_asset_path = None
    for asset_data in retargeted_assets:
        asset = asset_data.get_asset() if hasattr(asset_data, "get_asset") else None
        if not asset:
            package_name = str(asset_data.package_name)
            asset = unreal.EditorAssetLibrary.load_asset(package_name)
        if not asset:
            continue
        package_path = asset.get_path_name().split(".", 1)[0]
        class_name = asset.get_class().get_name() if asset else "Unknown"
        unreal.log(
            f"[AI4AnimationPy] retarget_output={package_path} class={class_name}"
        )
        if class_name == "AnimSequence":
            retargeted_anim_asset_path = package_path

    if not retargeted_anim_asset_path:
        raise RuntimeError("Retargeted AnimSequence asset was not produced.")

    target_anim_package = _normalize_asset_path(target_anim_asset)
    if retargeted_anim_asset_path != target_anim_package:
        if unreal.EditorAssetLibrary.does_asset_exist(target_anim_package):
            unreal.EditorAssetLibrary.delete_asset(target_anim_package)
        if not unreal.EditorAssetLibrary.rename_asset(
            retargeted_anim_asset_path,
            target_anim_package,
        ):
            raise RuntimeError(
                f"Failed to move retargeted animation to {target_anim_package}"
            )
        retargeted_anim_asset_path = target_anim_package

    _save_asset(retargeted_anim_asset_path)
    unreal.log(
        f"[AI4AnimationPy] final_retargeted_anim={retargeted_anim_asset_path}"
    )

    if os.environ.get("AI4A_QUIT_EDITOR", "0").strip() in {"1", "true", "True", "yes"}:
        unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - executes inside UE Python
        unreal.log_error(f"[AI4AnimationPy] {exc}")
        raise
