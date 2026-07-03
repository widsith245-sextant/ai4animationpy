import unreal


def main() -> None:
    names = [
        "IKRigDefinitionFactory",
        "IKRetargetFactory",
        "IKRigController",
        "IKRetargeterController",
        "IKRigDefinition",
        "IKRetargeter",
    ]
    for name in names:
        unreal.log(f"[AI4AnimationPy] has_{name}={hasattr(unreal, name)}")

    if hasattr(unreal, "IKRigController"):
        controller = unreal.IKRigController
        methods = sorted(name for name in dir(controller) if not name.startswith("_"))
        unreal.log(f"[AI4AnimationPy] IKRigController_methods={methods}")

    if hasattr(unreal, "IKRetargeterController"):
        controller = unreal.IKRetargeterController
        methods = sorted(name for name in dir(controller) if not name.startswith("_"))
        unreal.log(f"[AI4AnimationPy] IKRetargeterController_methods={methods}")


if __name__ == "__main__":
    main()
