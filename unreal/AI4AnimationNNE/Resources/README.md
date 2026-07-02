# AI4AnimationNNE Resources

Put exported ONNX bundles under `Resources/ModelPackages/<package-name>/`.

Expected files per package:

- `<package-name>.onnx`
- `<package-name>.ue.json`
- optional metadata sidecars copied from the Python export pipeline

The Unreal subsystem loads the `.ue.json` manifest first and then resolves the
ONNX file path relative to the manifest.
