"""Engineering facade exports for application-oriented integrations."""

from .Config import (
    ActorViewerConfig,
    MotionEditorConfig,
    ONNXExportConfig,
    SkeletonDefinition,
    UENNEBundleConfig,
)
from .Facade import EngineeringAPI
from .Programs import ActorViewerProgram, EmptyProgram, MotionEditorProgram
from .SOMAInterop import SOMAExportResult, export_skinned_soma_glb
from .UEInterop import UE_MANNY_TEST_MAPPING


def main(*args, **kwargs):
    from .CLI import main as _main

    return _main(*args, **kwargs)


__all__ = [
    "main",
    "ActorViewerConfig",
    "MotionEditorConfig",
    "ONNXExportConfig",
    "SkeletonDefinition",
    "UENNEBundleConfig",
    "EngineeringAPI",
    "ActorViewerProgram",
    "EmptyProgram",
    "MotionEditorProgram",
    "SOMAExportResult",
    "export_skinned_soma_glb",
    "UE_MANNY_TEST_MAPPING",
]
