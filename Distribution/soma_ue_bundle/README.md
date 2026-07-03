# SOMA UE 迁移分发包 (soma_ue_bundle)

本分发包用于把 SOMA 蒙皮骨架、SOMA 直导动画以及重定向到 UE5 Manny 的动画，直接迁移到任意 Unreal Engine 5.5 工程，供后续重定向 / 集成使用。

所有资产由 `ai4animationpy` 管线从 `Test_Animation/*.npz`（源全局旋转 `global_rot_mats` + `posed_joints`）经 `AI4AnimationNNEEditorLibrary.ImportClipFromJson` 导入生成，与上游 Kimodo SOMA skinning 语义一致。

## 目录结构

```
soma_ue_bundle/
├─ Content/AI4Animation/            拖入目标工程 Content/ 即可（保留 /Game/AI4Animation 路径）
│  ├─ SOMA/
│  │  ├─ SOMA_TestAnimation_Output1                (SkeletalMesh，SOMA 蒙皮骨架)
│  │  ├─ SOMA_TestAnimation_Output1_Skeleton       (Skeleton)
│  │  ├─ SOMA_TestAnimation_Output1_PhysicsAsset   (PhysicsAsset)
│  │  ├─ SOMA_TestAnimation_Output1_Anim           (基准直导动画)
│  │  ├─ SOMA_output1_Anim ... SOMA_Sleeping_Anim  (11 条 SOMA 直导 AnimSequence)
│  │  ├─ IK_SOMA_TestAnimation_Output1             (SOMA 源 IK Rig)
│  │  └─ RTG_SOMA_To_Manny                         (SOMA→Manny IK Retargeter)
│  └─ TestAnimations/
│     └─ AN_*_SOMA_Manny                           (重定向到 UE5 Manny 的 AnimSequence)
└─ Source/
   ├─ SOMA_TestAnimation_Output1.glb               (引擎中立蒙皮骨架 GLB，跨引擎重定向 / 重新导入用)
   └─ verification_report.json                     (11 条 clip 的 FK 位置误差报告)
```

## 迁移步骤

### 方式 A：直接拷贝 Content（推荐，最快）

1. 关闭目标 UE 工程编辑器。
2. 把 `Content/AI4Animation` 整个目录拷贝到目标工程的 `Content/` 下。
3. 重新打开编辑器，资产将出现在 `/Game/AI4Animation/...`。

> 说明：SOMA 资产间引用（Mesh↔Skeleton↔Anim↔Retargeter）均为 `/Game/AI4Animation/...` 相对内部路径，拷贝后引用保持完整。
> Manny 重定向资产 (`AN_*_SOMA_Manny`) 引用引擎自带的 `/Game/Characters/Mannequins/...`，需目标工程已启用 UE5 Manny（第三人称模板或 Mannequin 内容）。

### 方式 B：UE Migrate 工具

若目标工程已有部分同名资产，可在源工程中右键 `SOMA_TestAnimation_Output1` → Asset Actions → Migrate，交由 UE 自动处理依赖与冲突。

## 后续重定向

- **UE 内重定向**：直接使用 `RTG_SOMA_To_Manny`，或以 `IK_SOMA_TestAnimation_Output1` 为源新建到其它目标骨架的 IK Retargeter。
- **跨引擎 / 重新导入**：使用 `Source/SOMA_TestAnimation_Output1.glb`（含蒙皮权重与骨架层级）作为中立源。

## 资产清单与精度

| 类别 | 数量 |
|------|------|
| SOMA SkeletalMesh / Skeleton / PhysicsAsset | 各 1 |
| SOMA 直导 AnimSequence | 12（含基准 Output1） |
| SOMA→Manny 重定向 AnimSequence | 4 |
| IK Rig / Retargeter | 各 1 |

`Source/verification_report.json` 记录了每条 clip 用 `global_rot_mats` FK 重建关节位置与源 `posed_joints` 的误差，全部 < 0.0005 cm。

## 依赖前提

- Unreal Engine 5.5
- 目标工程启用 UE5 Manny（仅重定向后的 `AN_*_SOMA_Manny` 需要）
- 如需重新导入 / 重新生成，参见仓库根目录 `scripts/` 下的 `sync_all_soma_test_animations_into_nne_t.bat` 等脚本
