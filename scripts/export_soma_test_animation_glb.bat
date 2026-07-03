@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"
set "SKIN_NPZ=%REPO_ROOT%\skeletons\somaskel77\skin_standard.npz"
set "TPOSE_BVH=%REPO_ROOT%\skeletons\somaskel77\somaskel77_standard_tpose.bvh"
set "ANIM_BVH=%REPO_ROOT%\Test_Animation\output1.bvh"
set "OUTPUT_GLB=%REPO_ROOT%\Artifacts\UE\SOMA\SOMA_TestAnimation_Output1.glb"
set "OUTPUT_NPZ=%REPO_ROOT%\Artifacts\UE\SOMA\output1_source"

if not exist "%PYTHON_EXE%" (
    echo [AI4AnimationPy] ERROR: Python environment not found at %PYTHON_EXE%
    exit /b 1
)

if not exist "%SKIN_NPZ%" (
    echo [AI4AnimationPy] ERROR: SOMA skin file not found at %SKIN_NPZ%
    exit /b 1
)

if not exist "%TPOSE_BVH%" (
    echo [AI4AnimationPy] ERROR: SOMA T-pose BVH not found at %TPOSE_BVH%
    exit /b 1
)

if not exist "%ANIM_BVH%" (
    echo [AI4AnimationPy] ERROR: test animation BVH not found at %ANIM_BVH%
    exit /b 1
)

echo [AI4AnimationPy] Exporting SOMA skinned GLB and source NPZ...
"%PYTHON_EXE%" -m ai4animation.Engineering.CLI export-soma-glb "%SKIN_NPZ%" "%TPOSE_BVH%" "%OUTPUT_GLB%" --animation-bvh-path "%ANIM_BVH%" --output-motion-npz-path "%OUTPUT_NPZ%"
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Export complete.
exit /b 0
