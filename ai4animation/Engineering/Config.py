"""High-level engineering configuration objects for repeatable app startup."""

from dataclasses import dataclass, field
from typing import Any

from ai4animation.Animation.ContactModule import ContactModule
from ai4animation.Animation.GuidanceModule import GuidanceModule
from ai4animation.Animation.MirrorModule import MirrorModule
from ai4animation.Animation.MotionModule import MotionModule
from ai4animation.Animation.RootModule import RootModule
from ai4animation.Math import Vector3


def _normalize_mirror_axis(axis: tuple[float, float, float] | Any):
    if axis == (1.0, 0.0, 0.0):
        return Vector3.Axis.XPositive
    if axis == (0.0, 1.0, 0.0):
        return Vector3.Axis.YPositive
    if axis == (0.0, 0.0, 1.0):
        return Vector3.Axis.ZPositive
    return axis


@dataclass(frozen=True)
class SkeletonDefinition:
    """Stable skeleton contract used by editor, conversion, and export tooling."""

    name: str
    bone_names: tuple[str, ...]
    hip_name: str
    left_hip_name: str
    right_hip_name: str
    left_shoulder_name: str
    right_shoulder_name: str
    neck_name: str
    contact_pairs: tuple[tuple[str, float], ...] = ()
    mirror_axis: tuple[float, float, float] = (0.0, 0.0, 1.0)
    mirror_correction_euler: tuple[float, float, float] = (0.0, 0.0, 180.0)

    @classmethod
    def from_module(
        cls,
        name: str,
        module: Any,
        bone_names_attr: str = "FULL_BODY_NAMES",
        contact_threshold: float = 0.25,
    ) -> "SkeletonDefinition":
        contact_pairs: list[tuple[str, float]] = []
        for attr in (
            "LeftAnkleName",
            "LeftBallName",
            "RightAnkleName",
            "RightBallName",
        ):
            if hasattr(module, attr):
                contact_pairs.append((getattr(module, attr), contact_threshold))

        return cls(
            name=name,
            bone_names=tuple(getattr(module, bone_names_attr)),
            hip_name=module.HipName,
            left_hip_name=module.LeftHipName,
            right_hip_name=module.RightHipName,
            left_shoulder_name=module.LeftShoulderName,
            right_shoulder_name=module.RightShoulderName,
            neck_name=module.NeckName,
            contact_pairs=tuple(contact_pairs),
        )

    def create_modules(
        self,
        include_contacts: bool = True,
        include_guidance: bool = True,
        include_mirror: bool = True,
        proportional_contacts: bool = False,
    ) -> list:
        modules = [
            lambda motion: RootModule(
                motion,
                self.hip_name,
                self.left_hip_name,
                self.right_hip_name,
                self.left_shoulder_name,
                self.right_shoulder_name,
                self.neck_name,
            ),
            lambda motion: MotionModule(motion),
        ]

        if include_contacts and self.contact_pairs:
            contact_pairs = list(self.contact_pairs)
            modules.append(
                lambda motion: ContactModule(
                    motion,
                    contact_pairs,
                    proportional=proportional_contacts,
                )
            )

        if include_guidance:
            modules.append(lambda motion: GuidanceModule(motion))

        if include_mirror:
            axis = _normalize_mirror_axis(self.mirror_axis)
            correction = Vector3.Create(*self.mirror_correction_euler)
            modules.append(lambda motion: MirrorModule(motion, axis, correction))

        return modules

    def to_metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "bone_names": list(self.bone_names),
            "root_contract": {
                "hip_name": self.hip_name,
                "left_hip_name": self.left_hip_name,
                "right_hip_name": self.right_hip_name,
                "left_shoulder_name": self.left_shoulder_name,
                "right_shoulder_name": self.right_shoulder_name,
                "neck_name": self.neck_name,
            },
            "contact_pairs": [
                {"bone": bone_name, "velocity_threshold": threshold}
                for bone_name, threshold in self.contact_pairs
            ],
            "mirror": {
                "axis": list(self.mirror_axis),
                "correction_euler": list(self.mirror_correction_euler),
            },
        }


@dataclass(frozen=True)
class ActorViewerConfig:
    model_path: str
    skeleton: SkeletonDefinition
    entity_name: str = "Actor"
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    auto_rotate_degrees_per_second: float = 120.0


@dataclass(frozen=True)
class MotionEditorConfig:
    dataset_directory: str
    model_path: str
    skeleton: SkeletonDefinition
    entity_name: str = "MotionEditor"
    include_contacts: bool = True
    include_guidance: bool = True
    include_mirror: bool = True
    proportional_contacts: bool = False
    max_files: int | None = None

    def create_modules(self) -> list:
        return self.skeleton.create_modules(
            include_contacts=self.include_contacts,
            include_guidance=self.include_guidance,
            include_mirror=self.include_mirror,
            proportional_contacts=self.proportional_contacts,
        )


@dataclass(frozen=True)
class ONNXExportConfig:
    output_path: str
    input_name: str = "input"
    output_name: str = "output"
    opset_version: int = 17
    dynamic_batch: bool = True
    metadata_path: str | None = None


@dataclass(frozen=True)
class UENNEBundleConfig:
    package_name: str
    onnx_path: str
    manifest_path: str
    skeleton: SkeletonDefinition
    source_checkpoint: str | None = None
    dataset_directory: str | None = None
    sample_rate: int | None = None
    metadata_path: str | None = None
    runtime_name: str = "NNERuntimeORTCpu"
    primary_ue_skeleton: str = "UE5 Manny/Quinn"
    supports_custom_skeletons: bool = True
    compatible_input_formats: tuple[str, ...] = ("npz", "bvh")
    terrain_supports_slope: bool = True
    terrain_supports_height_variation: bool = True
    preserve_relative_paths: bool = False
    extra_metadata: dict[str, Any] = field(default_factory=dict)
