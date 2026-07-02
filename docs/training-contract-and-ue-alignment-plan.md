# Training Contract and UE Alignment Plan

## Problem Statement

We now have:

- a Python-side authoring and export pipeline in this repository
- a project-level Unreal plugin deployed into `D:\PCG_ANIM_RL\NNE_T`
- ONNX export working for the first locomotion sample

The remaining gap is not basic export anymore. The gap is contract stability:

- Python training features must be versioned and reproducible.
- Unreal preprocessing must match Python feature ordering exactly.
- Manny/Quinn and custom skeleton retargeting must fit the same package format.
- Terrain and slope awareness must move from design intent into explicit feature contracts.

## Capability Boundary

Python owns:

- source motion import from BVH, FBX, GLB, NPZ
- dataset normalization
- feature extraction
- training
- ONNX export
- package manifest generation
- offline contract validation

Unreal owns:

- package ingestion
- ONNX loading through NNE
- runtime feature gathering
- retargeting to Manny/Quinn or custom skeletons
- Motion Matching integration
- IK/FK and morph-based postprocess
- terrain-aware gameplay presentation

## Assumptions

- The first runtime target remains `NNERuntimeORTCpu`.
- The first canonical UE skeleton target is `UE5 Manny/Quinn`.
- Custom skeletons are supported through UE native retargeting, not a separate Python-specific runtime format.
- Training continues to happen in gym-like environments rooted in this repository.
- Terrain variation matters and must become part of the observation contract rather than a later patch.

## Unified Artifact List

Each model package should be treated as one versioned unit:

- `model.onnx`
- `model.metadata.json`
- `model.ue.json`
- `feature_contract.json`
- `normalization_contract.json`
- `skeleton_contract.json`
- optional fixture inputs and expected outputs for UE parity tests

Recommended package fields:

- package id
- semantic version
- source checkpoint path
- source dataset summary
- sample rate
- supported raw input formats
- training feature layout
- output feature layout
- normalization statistics
- terrain feature definition
- retargeting guidance
- runtime target name

## Layer Mapping

### 1. Unified content source

Primary truth:

- `Definitions.py`-derived skeleton contracts
- converted `NPZ` motions
- package manifest and feature contract JSON

This avoids keeping separate hand-maintained definitions in:

- Python demos
- Unreal blueprints
- ad hoc notes

### 2. Offline build and validation tools

Python tools should produce:

- motion conversion reports
- dataset summaries
- contract JSON
- ONNX packages
- parity fixtures for UE

Recommended additions:

- `ai4animation/Engineering/Contracts.py`
- `ai4animation/Engineering/Validation.py`
- `scripts/validate_ue_contract.bat`

### 3. Unreal ingestion

The current plugin already follows the right shape:

- one subsystem
- one Blueprint library
- one project settings object
- one package manifest format

Next Unreal additions should stay narrow:

- load `feature_contract.json`
- expose expected input tensor element count
- add a C++ preprocessing path that builds the NNE input buffer from character state
- add a debug widget or log dump that compares runtime feature vectors against fixture JSON

### 4. Operations and governance

Treat these as normal development assets:

- package versioning
- contract schema version
- ONNX export compatibility notes
- local parity test outputs
- documented fallback when model load fails

## Training Contract Proposal

## Input Contract

Split the model input into named feature groups, not only raw flattened tensors.

Minimum group set for locomotion:

1. `current_pose`
   - root-relative joint positions
   - root-relative forward axes
   - root-relative up axes
2. `current_velocity`
   - root-relative joint velocities
3. `trajectory_future`
   - future root positions on XZ
   - future facing directions on XZ
   - future root velocities on XZ
4. `guidance`
   - style or pose guidance vectors
5. `terrain`
   - ground height samples
   - slope normal samples
   - optional foothold confidence
6. `contacts_optional`
   - current or predicted contact hints if required by a downstream postprocess model

## Terrain Contract

Terrain must stop being implicit.

Recommended first terrain features:

- local ground heights sampled along the future trajectory
- local surface normals sampled at the same points
- signed slope angles relative to root forward/right axes
- optional foot target offsets against terrain

These features should be:

- generated in gyms during training
- exported into the feature contract JSON
- reproduced in UE from traces or terrain queries

## Output Contract

For the first UE slice, the output should stay compact and runtime-friendly.

Recommended output groups:

1. `future_root_delta`
2. `future_root_direction`
3. `future_joint_positions`
4. `future_joint_rotations`
5. `future_joint_velocities`
6. optional `contact_logits`

Unreal should then own:

- retarget application
- motion matching selection or blending
- IK/FK cleanup
- morph or deformation postprocess

## Unreal Alignment Plan

### Preprocess path

Implement one C++ feature builder in the plugin:

- reads current skeletal pose
- gathers root-space transforms
- samples terrain under future trajectory probes
- emits the exact flattened float array expected by Python

Do not spread this logic across multiple Blueprints.

### Retarget path

Use:

- Manny/Quinn as canonical first target
- UE IK Retargeter for custom skeleton mapping

Keep the Python package skeleton contract authoritative for training order.
Keep UE retargeting authoritative for presentation skeleton differences.

### Postprocess path

Let UE native systems handle:

- Motion Matching
- Control Rig
- IKRig
- FK cleanup
- morph-based deformation

The ONNX package should not try to duplicate those systems.

## Execution Order

1. Freeze the first locomotion feature contract from the current Geno package.
2. Export that contract into machine-readable JSON next to the current `.ue.json`.
3. Add UE-side C++ preprocessing that consumes the same contract.
4. Add one parity test fixture:
   - Python writes sample input vector and expected output vector.
   - UE runs the same model and compares within tolerance.
5. Add terrain feature group to gym training and package schema.
6. Introduce Manny/Quinn runtime preview in `NNE_T`.

## Acceptance Criteria

The next slice is complete only if:

- one package contains explicit feature and skeleton contracts
- UE loads the package without hand edits
- UE feature preprocessing matches Python ordering
- one fixture parity check passes
- Manny/Quinn can consume the runtime output path
- custom skeleton support is documented via UE retargeting
- terrain features exist in both training and runtime contracts

## Next Smallest Follow-up Slice

Build one closed loop:

- export `feature_contract.json` for `geno-biped-locomotion`
- add plugin-side contract loader
- add one `BuildInputTensorFromDebugState(...)` C++ function
- add one UE debug command that runs inference and logs tensor sizes and first values

That gives us the smallest reliable bridge before expanding into full AnimGraph integration.
