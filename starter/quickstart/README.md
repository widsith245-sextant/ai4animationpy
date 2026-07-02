# Engineering Quickstart

This folder provides application-level starter scripts built on top of the new
`ai4animation.Engineering` facade.

## Scripts

- `cranberry_actor_viewer.py`
  - Starts a stable actor-viewer app using the Cranberry demo skeleton.
- `cranberry_motion_editor.py`
  - Starts the motion editor with a reusable config instead of a one-off demo.
- `export_ue_nne_bundle.py`
  - Exports the biped locomotion checkpoint to ONNX and writes a UE/NNE bundle
    manifest into `Artifacts/UE`.

## CLI equivalents

After installing the package, the same workflows are available through:

```bash
ai4a actor --definitions-path /abs/path/to/Definitions.py /abs/path/to/Model.glb
ai4a editor --definitions-path /abs/path/to/Definitions.py /abs/path/to/NPZ /abs/path/to/Model.glb
ai4a export-onnx /abs/path/to/Network.pt /abs/path/to/output.onnx --shape 1,324
ai4a ue-manifest /abs/path/to/output.onnx /abs/path/to/output.ue.json --definitions-path /abs/path/to/Definitions.py
```
