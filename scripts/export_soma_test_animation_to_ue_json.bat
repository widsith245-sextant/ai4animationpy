@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "SOURCE_NPZ=%~1"
if "%SOURCE_NPZ%"=="" set "SOURCE_NPZ=%REPO_ROOT%\Test_Animation\output1.npz"

set "OUTPUT_JSON=%~2"
if "%OUTPUT_JSON%"=="" set "OUTPUT_JSON=%REPO_ROOT%\Artifacts\UE\SOMA\BatchJson\output1.json"

set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"
set "SKIN_NPZ=%REPO_ROOT%\skeletons\somaskel77\skin_standard.npz"
set "TPOSE_BVH=%REPO_ROOT%\skeletons\somaskel77\somaskel77_standard_tpose.bvh"

if not exist "%PYTHON_EXE%" (
    echo [AI4AnimationPy] ERROR: Python environment not found at %PYTHON_EXE%
    exit /b 1
)

if not exist "%SOURCE_NPZ%" (
    echo [AI4AnimationPy] ERROR: source SOMA test animation not found: %SOURCE_NPZ%
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

echo [AI4AnimationPy] Exporting SOMA test animation to UE direct-import JSON...
"%PYTHON_EXE%" -m ai4animation.Engineering.CLI export-soma-ue-json "%SOURCE_NPZ%" "%SKIN_NPZ%" "%OUTPUT_JSON%" --skeleton-asset "/Game/AI4Animation/SOMA/SOMA_TestAnimation_Output1_Skeleton" --preview-mesh-asset "/Game/AI4Animation/SOMA/SOMA_TestAnimation_Output1"
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Wrote %OUTPUT_JSON%
exit /b 0
