from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ai4animation.Animation.Motion import Motion
from ai4animation.Engineering.SOMAInterop import _extract_translation_rotation, _world_to_local_matrices
from ai4animation.Engineering.UEInterop import (
    _convert_positions_to_unreal_cm,
    _convert_quaternions_to_unreal_basis,
)
from ai4animation.Math import Quaternion


def _quat_multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ax, ay, az, aw = np.moveaxis(a, -1, 0)
    bx, by, bz, bw = np.moveaxis(b, -1, 0)
    return np.stack(
        [
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz,
        ],
        axis=-1,
    )


def _quat_rotate(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    q_xyz = q[..., :3]
    qw = q[..., 3:4]
    t = 2.0 * np.cross(q_xyz, v)
    return v + qw * t + np.cross(q_xyz, t)


def _safe_name(value: str) -> str:
    import re

    normalized = re.sub(r"[^0-9A-Za-z_]+", "_", value.strip())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "SOMA_Clip"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    test_dir = repo_root / "Test_Animation"
    skin_path = repo_root / "skeletons" / "somaskel77" / "skin_standard.npz"
    tpose_path = repo_root / "skeletons" / "somaskel77" / "somaskel77_standard_tpose.bvh"
    report_path = repo_root / "Artifacts" / "UE" / "SOMA" / "verification_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    skin = np.load(skin_path, allow_pickle=True)
    joint_names = [str(x) for x in skin["rig_joint_names"].tolist()]
    bind_global = np.asarray(skin["bind_rig_transform"], dtype=np.float32)

    tpose = Motion.LoadFromBVH(str(tpose_path), scale=0.01)
    full_names = list(tpose.Hierarchy.BoneNames)
    name_to = {name: index for index, name in enumerate(full_names)}
    parent_indices: list[int] = []
    for name in joint_names:
        parent_name = tpose.Hierarchy.ParentNames[name_to[name]]
        parent_indices.append(joint_names.index(parent_name) if parent_name in joint_names else -1)

    bind_local = _world_to_local_matrices(bind_global[None, ...], parent_indices)[0]
    bind_local_positions, _ = _extract_translation_rotation(bind_local)
    bind_local_positions_ue = _convert_positions_to_unreal_cm(bind_local_positions)

    results = []
    for npz_path in sorted(test_dir.glob("*.npz")):
        data = np.load(npz_path, allow_pickle=True)
        world_positions_target = _convert_positions_to_unreal_cm(
            np.asarray(data["posed_joints"], dtype=np.float32)
        )
        num_frames, num_joints = world_positions_target.shape[:2]

        local_rotations = _convert_quaternions_to_unreal_basis(
            Quaternion.FromMatrix(np.asarray(data["local_rot_mats"], dtype=np.float32))
        )
        local_world_positions = np.zeros((num_frames, num_joints, 3), dtype=np.float32)
        local_world_rotations = np.zeros((num_frames, num_joints, 4), dtype=np.float32)
        local_world_positions[:, 0] = world_positions_target[:, 0]
        local_world_rotations[:, 0] = local_rotations[:, 0]

        for joint_index in range(1, num_joints):
            parent_index = parent_indices[joint_index]
            local_world_rotations[:, joint_index] = _quat_multiply(
                local_world_rotations[:, parent_index],
                local_rotations[:, joint_index],
            )
            local_world_positions[:, joint_index] = local_world_positions[:, parent_index] + _quat_rotate(
                local_world_rotations[:, parent_index],
                np.broadcast_to(bind_local_positions_ue[joint_index], (num_frames, 3)),
            )

        local_errors = np.linalg.norm(local_world_positions - world_positions_target, axis=-1)

        global_rotations = _convert_quaternions_to_unreal_basis(
            Quaternion.FromMatrix(np.asarray(data["global_rot_mats"], dtype=np.float32))
        )
        global_world_positions = np.zeros((num_frames, num_joints, 3), dtype=np.float32)
        global_world_positions[:, 0] = world_positions_target[:, 0]
        for joint_index in range(1, num_joints):
            parent_index = parent_indices[joint_index]
            global_world_positions[:, joint_index] = global_world_positions[:, parent_index] + _quat_rotate(
                global_rotations[:, parent_index],
                np.broadcast_to(bind_local_positions_ue[joint_index], (num_frames, 3)),
            )

        global_errors = np.linalg.norm(global_world_positions - world_positions_target, axis=-1)

        results.append(
            {
                "source_npz": str(npz_path),
                "suggested_asset_name": f"SOMA_{_safe_name(npz_path.stem)}_Anim",
                "num_frames": int(num_frames),
                "local_fk_mean_position_error_cm": float(local_errors.mean()),
                "local_fk_max_position_error_cm": float(local_errors.max()),
                "global_fk_mean_position_error_cm": float(global_errors.mean()),
                "global_fk_max_position_error_cm": float(global_errors.max()),
            }
        )

    summary = {
        "count": len(results),
        "max_local_fk_mean_position_error_cm": max(
            item["local_fk_mean_position_error_cm"] for item in results
        ),
        "max_local_fk_position_error_cm": max(
            item["local_fk_max_position_error_cm"] for item in results
        ),
        "max_global_fk_mean_position_error_cm": max(
            item["global_fk_mean_position_error_cm"] for item in results
        ),
        "max_global_fk_position_error_cm": max(
            item["global_fk_max_position_error_cm"] for item in results
        ),
        "results": results,
    }
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(report_path)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
