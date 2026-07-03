@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "TARGET_PROJECT=%~1"
if "%TARGET_PROJECT%"=="" set "TARGET_PROJECT=D:\PCG_ANIM_RL\NNE_T"

set "JSON_DIR=%REPO_ROOT%\Artifacts\UE\SOMA\BatchJson"
set "SOMA_MESH=%TARGET_PROJECT%\Content\AI4Animation\SOMA\SOMA_TestAnimation_Output1.uasset"
set "SOMA_SKELETON=%TARGET_PROJECT%\Content\AI4Animation\SOMA\SOMA_TestAnimation_Output1_Skeleton.uasset"

call "%~dp0verify_soma_test_animation_contract.bat"
if errorlevel 1 exit /b 1

if exist "%SOMA_MESH%" if exist "%SOMA_SKELETON%" (
    echo [AI4AnimationPy] Existing SOMA source assets found. Skipping GLB source re-import.
) else (
    call "%~dp0import_soma_test_animation_into_nne_t.bat" "%TARGET_PROJECT%"
    if errorlevel 1 exit /b 1
)

call "%~dp0export_all_soma_test_animations_to_ue_json.bat" "%REPO_ROOT%\Test_Animation" "%JSON_DIR%"
if errorlevel 1 exit /b 1

call "%~dp0import_all_soma_test_animations_into_nne_t.bat" "%TARGET_PROJECT%" "%JSON_DIR%"
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Full SOMA test animation sync complete.
exit /b 0
