@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "TARGET_PROJECT=%~1"
if "%TARGET_PROJECT%"=="" set "TARGET_PROJECT=D:\PCG_ANIM_RL\NNE_T"

set "REPORT=%REPO_ROOT%\Artifacts\UE\SOMA\verification_report.json"
if not exist "%REPORT%" (
    echo [AI4AnimationPy] ERROR: Verification report not found at %REPORT%
    exit /b 1
)

echo [AI4AnimationPy] Retargeting all SOMA JSON-imported clips to Manny...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ErrorActionPreference='Stop';" ^
    "$report = Get-Content -Raw '%REPORT%' | ConvertFrom-Json;" ^
    "foreach ($entry in $report.results) {" ^
    "  $stem = [System.IO.Path]::GetFileNameWithoutExtension($entry.source_npz);" ^
    "  $safe = (($stem -replace '[^0-9A-Za-z_]+', '_') -replace '_+', '_').Trim('_');" ^
    "  if ([string]::IsNullOrWhiteSpace($safe)) { $safe = 'SOMA_Clip' };" ^
    "  $sourceAnim = '/Game/AI4Animation/SOMA/SOMA_' + $safe + '_Anim';" ^
    "  $targetAnim = '/Game/AI4Animation/TestAnimations/AN_' + $safe + '_SOMA_Manny';" ^
    "  Write-Host ('[AI4AnimationPy] Retargeting ' + $stem + ' -> ' + $targetAnim);" ^
    "  $env:AI4A_SOMA_SOURCE_ANIM = $sourceAnim;" ^
    "  $env:AI4A_SOMA_TARGET_ANIM = $targetAnim;" ^
    "  & '%~dp0retarget_soma_to_manny_in_nne_t.bat' '%TARGET_PROJECT%';" ^
    "  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE };" ^
    "};"
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Retargeted all SOMA clips to Manny.
exit /b 0
