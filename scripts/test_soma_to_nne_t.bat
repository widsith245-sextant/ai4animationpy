@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "TARGET_PROJECT=%~1"
if "%TARGET_PROJECT%"=="" set "TARGET_PROJECT=D:\PCG_ANIM_RL\NNE_T"
set "UPROJECT=%TARGET_PROJECT%\NNE_T.uproject"
set "EDITOR_CMD=D:\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
set "INSPECT_SCRIPT=%REPO_ROOT%\unreal\Python\inspect_animation_asset.py"
set "AI4A_INSPECT_ASSET=/Game/AI4Animation/TestAnimations/AN_TestAnimation_Output1_SOMA_Manny"

if not exist "%UPROJECT%" (
    echo [AI4AnimationPy] ERROR: Unreal project not found at %UPROJECT%
    exit /b 1
)

if not exist "%EDITOR_CMD%" (
    echo [AI4AnimationPy] ERROR: UnrealEditor-Cmd.exe not found at %EDITOR_CMD%
    exit /b 1
)

if not exist "%INSPECT_SCRIPT%" (
    echo [AI4AnimationPy] ERROR: Unreal Python inspect script not found at %INSPECT_SCRIPT%
    exit /b 1
)

call "%~dp0export_soma_test_animation_glb.bat"
if errorlevel 1 exit /b 1

call "%~dp0import_soma_test_animation_into_nne_t.bat" "%TARGET_PROJECT%"
if errorlevel 1 exit /b 1

call "%~dp0retarget_soma_to_manny_in_nne_t.bat" "%TARGET_PROJECT%"
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Inspecting final Manny animation asset...
"%EDITOR_CMD%" "%UPROJECT%" -run=pythonscript -script="%INSPECT_SCRIPT%" -unattended -nop4 -nosplash -nullrhi
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] SOMA to Manny pipeline completed for %TARGET_PROJECT%.
exit /b 0
