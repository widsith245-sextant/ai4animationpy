@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "INPUT_DIR=%~1"
if "%INPUT_DIR%"=="" set "INPUT_DIR=%REPO_ROOT%\Test_Animation"

set "OUTPUT_DIR=%~2"
if "%OUTPUT_DIR%"=="" set "OUTPUT_DIR=%REPO_ROOT%\Artifacts\UE\SOMA\BatchJson"

set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"
set "SKIN_NPZ=%REPO_ROOT%\skeletons\somaskel77\skin_standard.npz"
set "TPOSE_BVH=%REPO_ROOT%\skeletons\somaskel77\somaskel77_standard_tpose.bvh"

if not exist "%PYTHON_EXE%" (
    echo [AI4AnimationPy] ERROR: Python environment not found at %PYTHON_EXE%
    exit /b 1
)

if not exist "%INPUT_DIR%" (
    echo [AI4AnimationPy] ERROR: Test animation directory not found at %INPUT_DIR%
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

echo [AI4AnimationPy] Exporting all SOMA test animations from %INPUT_DIR% ...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ErrorActionPreference='Stop';" ^
    "$python = '%PYTHON_EXE%';" ^
    "$inputDir = '%INPUT_DIR%';" ^
    "$outputDir = '%OUTPUT_DIR%';" ^
    "$skin = '%SKIN_NPZ%';" ^
    "$tpose = '%TPOSE_BVH%';" ^
    "New-Item -ItemType Directory -Force -Path $outputDir | Out-Null;" ^
    "Get-ChildItem -LiteralPath $inputDir -Filter '*.npz' | Sort-Object Name | ForEach-Object {" ^
    "  $stem = [System.IO.Path]::GetFileNameWithoutExtension($_.Name);" ^
    "  $safe = (($stem -replace '[^0-9A-Za-z_]+', '_') -replace '_+', '_').Trim('_');" ^
    "  if ([string]::IsNullOrWhiteSpace($safe)) { $safe = 'SOMA_Clip' };" ^
    "  $out = Join-Path $outputDir ($safe + '.json');" ^
    "  & $python -m ai4animation.Engineering.CLI export-soma-ue-json $_.FullName $skin $out --skeleton-asset '/Game/AI4Animation/SOMA/SOMA_TestAnimation_Output1_Skeleton' --preview-mesh-asset '/Game/AI4Animation/SOMA/SOMA_TestAnimation_Output1';" ^
    "  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE };" ^
    "  Write-Host ('[AI4AnimationPy] Exported ' + $_.Name + ' -> ' + $out);" ^
    "};"
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Exported all SOMA test animation JSON payloads to %OUTPUT_DIR%
exit /b 0
