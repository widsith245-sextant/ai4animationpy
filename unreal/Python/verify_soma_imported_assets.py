"""Verify SOMA AnimSequence assets imported into the UE project."""

from __future__ import annotations

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


def main() -> None:
    report_path = Path(_required_env("AI4A_VERIFY_REPORT")).resolve()
    destination = os.environ.get("AI4A_IMPORT_DEST", "/Game/AI4Animation/SOMA").strip().rstrip("/")
    skeleton_path = os.environ.get(
        "AI4A_IMPORT_SKELETON",
        "/Game/AI4Animation/SOMA/SOMA_TestAnimation_Output1_Skeleton.SOMA_TestAnimation_Output1_Skeleton",
    ).strip()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    expected_skeleton = skeleton_path.split(".", 1)[0]

    failures: list[str] = []
    checked = 0

    for entry in report["results"]:
        clip_stem = Path(entry["source_npz"]).stem
        asset_name = f"SOMA_{_safe_asset_name(clip_stem)}_Anim"
        asset_path = f"{destination}/{asset_name}.{asset_name}"

        if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            failures.append(f"Missing asset: {asset_path}")
            continue

        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if not asset:
            failures.append(f"Failed to load asset: {asset_path}")
            continue

        if asset.get_class().get_name() != "AnimSequence":
            failures.append(f"Wrong asset class for {asset_path}: {asset.get_class().get_name()}")
            continue

        skeleton = asset.get_editor_property("skeleton")
        if not skeleton:
            failures.append(f"Missing skeleton on {asset_path}")
            continue

        skeleton_package = skeleton.get_path_name().split(".", 1)[0]
        if skeleton_package != expected_skeleton:
            failures.append(
                f"Unexpected skeleton on {asset_path}: {skeleton_package} != {expected_skeleton}"
            )

        num_frames = int(entry["num_frames"])
        frame_rate = 30.0
        expected_length = (num_frames - 1) / frame_rate if num_frames > 0 else 0.0
        actual_length = float(asset.get_editor_property("sequence_length"))
        if abs(actual_length - expected_length) > 0.05:
            failures.append(
                f"Sequence length mismatch for {asset_path}: "
                f"expected ~{expected_length:.3f}s, got {actual_length:.3f}s"
            )

        checked += 1
        unreal.log(
            f"[AI4AnimationPy] verified asset={asset_path} "
            f"frames={num_frames} length={actual_length:.3f}s"
        )

    if failures:
        for message in failures:
            unreal.log_error(f"[AI4AnimationPy] {message}")
        raise RuntimeError(f"SOMA import verification failed with {len(failures)} issue(s).")

    unreal.log(f"[AI4AnimationPy] Verified {checked} SOMA AnimSequence assets.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - executes inside UE Python
        unreal.log_error(f"[AI4AnimationPy] {exc}")
        raise
