# AI4AnimationPy Repository Architecture and UE/NNE Migration Plan

## 1. What this repository already contains

The repository is split into two practical halves:

- `ai4animation/`
  - The reusable runtime and data-processing framework.
- `Demos/`
  - Example programs showing how to combine the low-level pieces.

Inside the package, the main areas are:

- `AI4Animation.py`
  - Engine bootstrap and execution mode selector (`STANDALONE`, `HEADLESS`, `MANUAL`).
- `Scene.py`, `Entity.py`, `Components/`
  - ECS runtime for scene graph ownership and per-frame callbacks.
- `Animation/`
  - Motion storage, datasets, feature modules, and time-series logic.
- `Math/`
  - Vectorized math wrappers for transforms, vectors, rotations, and quaternions.
- `Import/`
  - GLB, FBX, BVH import plus recursive batch conversion to NPZ.
- `AI/`
  - Sampling, training helpers, model implementations, and tensor read/feed helpers.
- `Standalone/`
  - Optional raylib renderer and immediate-mode GUI.
- `IK/`
  - FABRIK inverse kinematics support.

## 2. Real runtime architecture in this codebase

The actual execution flow is:

1. `AI4Animation` bootstraps the runtime and chooses an execution mode.
2. A `Program` object receives `Start`, `Update`, `Draw`, and `GUI` callbacks.
3. The `Scene` owns `Entity` instances.
4. Each `Entity` owns `Component` instances such as `Actor` or `MotionEditor`.
5. Animation data enters through `Motion` and `Dataset`.
6. Feature extraction is attached by `Module` subclasses such as:
   - `RootModule`
   - `MotionModule`
   - `ContactModule`
   - `GuidanceModule`
   - `MirrorModule`
7. Training and inference consume the generated features through `FeedTensor`,
   model classes, and `ReadTensor`.

The important observation is that this repository is already strongly layered,
but its top-level usage is still demo-centric. Each demo hand-wires the same
kind of setup logic again:

- load definitions
- define root/contact/mirror modules
- create datasets
- create actors/editors
- choose runtime mode

That is why application integration feels heavier than it should.

## 3. Engineering facade added in this workspace

To reduce that friction, a new package was added:

- `ai4animation/Engineering/`

It introduces four stable surfaces:

- `Config.py`
  - Declarative config objects such as `SkeletonDefinition`,
    `MotionEditorConfig`, and `ONNXExportConfig`.
- `Programs.py`
  - Reusable `ActorViewerProgram` and `MotionEditorProgram`.
- `Facade.py`
  - High-level `EngineeringAPI` for loading motions, converting directories,
    summarizing datasets, launching apps, exporting ONNX, and writing UE/NNE manifests.
- `CLI.py`
  - Application-facing CLI entry point exposed as `ai4a`.

This layer keeps the original ECS untouched while giving external applications a
repeatable integration surface.

## 4. Quickstart paths now available

There are now three engineering quickstarts:

- `starter/quickstart/cranberry_actor_viewer.py`
  - Minimal stable actor viewer.
- `starter/quickstart/cranberry_motion_editor.py`
  - Motion editor bootstrapped from a config contract.
- `starter/quickstart/export_ue_nne_bundle.py`
  - Example ONNX export plus UE/NNE bundle manifest generation.

There is also a CLI:

- `ai4a convert`
- `ai4a inspect-motion`
- `ai4a dataset-summary`
- `ai4a actor`
- `ai4a editor`
- `ai4a export-onnx`
- `ai4a ue-manifest`

## 5. Current gaps for Unreal migration

The repository is close to a strong authoring and training environment, but UE
integration still needs a deliberate delivery boundary.

Current gaps:

- There is no official ONNX export contract in the original package.
- There is no manifest describing feature order, sample rate, and skeleton
  contracts for downstream runtimes.
- Demo programs mix authoring concerns with runtime concerns.
- The feature contract is implicit in Python code such as `FeedTensor` order,
  not yet versioned for external consumers.

## 6. Target architecture for UE + ONNX + NNE

Use a four-layer architecture.

### Layer A. Unified content source

Authoritative sources:

- skeleton definitions
- motion NPZ datasets
- training feature contract
- model statistics and export metadata

Recommended artifacts:

- `Definitions.py` or a future neutral skeleton schema
- converted `.npz` motion corpus
- `feature_contract.json`
- `training_stats.json`
- `network.onnx`
- `network.ue.json`

### Layer B. Python build and validation tools

Python remains the authoring and validation side.

Responsibilities:

- motion conversion
- dataset validation
- feature extraction
- training
- ONNX export
- manifest generation

Recommended Python modules:

- `engineering.convert`
- `engineering.dataset`
- `engineering.export.onnx`
- `engineering.export.manifest`
- `engineering.validate.contract`

### Layer C. Unreal ingestion

Unreal should stay focused on runtime ownership and presentation.

Recommended UE surface:

- one `UAI4AnimationNNEAsset` data asset for file references and metadata
- one `UAI4AnimationNNESubsystem` for model/session ownership
- one `UBlueprintFunctionLibrary` or C++ facade for inference calls
- versioned DTO structs for:
  - skeleton contract
  - model input contract
  - model output contract
  - postprocess settings

Unreal should not recreate Python feature logic ad hoc in Blueprint.
Instead, the feature contract should be exported once and reimplemented in a
small C++ preprocessing layer that matches Python exactly.

### Layer D. Observability and governance

Require from the start:

- model package versioning
- manifest schema version
- latency measurement for preprocess + inference + postprocess
- dataset provenance in the exported manifest
- explicit fallback behavior when NNE model load fails

## 7. Recommended bridge contract for NNE

To keep UE inference trustworthy, the contract between Python and Unreal should
be explicit and versioned.

Minimum manifest fields:

- package name
- schema version
- source checkpoint
- ONNX path
- sample rate
- skeleton bone order
- contact pair definitions
- input tensor name
- output tensor name
- input feature layout
- output feature layout
- normalization/statistics payload location
- postprocess requirements

The new `EngineeringAPI.write_ue_nne_bundle(...)` starts that process by writing
the package, skeleton, dataset summary, and preprocess requirements into a
versioned JSON manifest.

## 8. Migration path

### Phase 1. Stabilize authoring contracts

- Treat `SkeletonDefinition` as the project-side source of truth.
- Convert raw source motions to NPZ once.
- Write dataset summaries and validation reports.
- Freeze input/output feature ordering per model family.

### Phase 2. Export deployable model bundles

- Export ONNX from the chosen PyTorch checkpoints.
- Export matching metadata and normalization payloads.
- Generate a UE/NNE manifest bundle per exported model.

### Phase 3. Build the Unreal runtime bridge

- Implement feature preprocessing in C++.
- Load ONNX with NNE.
- Map outputs into pose DTOs or control trajectories.
- Keep IK, foot locking, and animation graph integration on the UE side.

### Phase 4. Close the verification loop

- compare Python and UE inference outputs on the same fixtures
- add latency and correctness regression tests
- version every model package and skeleton contract

## 9. Acceptance criteria for the first UE slice

The first slice should be intentionally narrow:

- one skeleton
- one dataset family
- one trained model
- one ONNX export path
- one UE runtime loader
- one deterministic preprocess test
- one visible in-engine playback result

Recommended first slice:

- Geno biped locomotion checkpoint
- exported ONNX
- UE subsystem loads model
- UE C++ preprocess reproduces Python `FeedTensor` ordering
- output drives a debug animation pose or trajectory preview

## 10. Feedback points to confirm with stakeholders

Before the next iteration, confirm:

1. Is the first UE target character `Geno`, `Cranberry`, or your own skeleton?
2. Do you want UE to own only inference, or also part of the postprocess/IK stack?
3. Should the first NNE slice target offline validation, editor preview, or real-time gameplay?
