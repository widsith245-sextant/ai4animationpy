@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "SOURCE_BVH=%~1"
if "%SOURCE_BVH%"=="" set "SOURCE_BVH=%REPO_ROOT%\Test_Animation\output1.bvh"

set "OUTPUT_JSON=%~2"
if "%OUTPUT_JSON%"=="" set "OUTPUT_JSON=%REPO_ROOT%\Artifacts\UE\TestAnimation\output1_manny_import.json"

set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    echo [AI4AnimationPy] ERROR: Python environment not found. Run scripts\bootstrap_env.bat first.
    exit /b 1
)

if not exist "%SOURCE_BVH%" (
    echo [AI4AnimationPy] ERROR: source animation not found: %SOURCE_BVH%
    exit /b 1
)

echo [AI4AnimationPy] Exporting %SOURCE_BVH% to Manny import JSON...
"%PYTHON_EXE%" -m ai4animation.Engineering.CLI export-ue-clip "%SOURCE_BVH%" "%OUTPUT_JSON%"
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Wrote %OUTPUT_JSON%
exit /b 0
