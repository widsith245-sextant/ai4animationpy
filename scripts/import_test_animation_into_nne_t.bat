@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "TARGET_PROJECT=%~1"
if "%TARGET_PROJECT%"=="" set "TARGET_PROJECT=D:\PCG_ANIM_RL\NNE_T"

set "UPROJECT=%TARGET_PROJECT%\NNE_T.uproject"
set "EDITOR_CMD=D:\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
set "PY_SCRIPT=%REPO_ROOT%\unreal\Python\import_test_animation_to_project.py"

set "AI4A_IMPORT_JSON=%~2"
if "%AI4A_IMPORT_JSON%"=="" set "AI4A_IMPORT_JSON=%REPO_ROOT%\Artifacts\UE\TestAnimation\output1_manny_import.json"
set "AI4A_IMPORT_DEST=/Game/AI4Animation/TestAnimations"
set "AI4A_IMPORT_ASSET=AN_TestAnimation_Output1_Manny"
set "AI4A_IMPORT_SKELETON=/Game/Characters/Mannequins/Meshes/SK_Mannequin.SK_Mannequin"
set "AI4A_IMPORT_PREVIEW_MESH=/Game/Characters/Mannequins/Meshes/SKM_Manny.SKM_Manny"

if not exist "%UPROJECT%" (
    echo [AI4AnimationPy] ERROR: Unreal project not found at %UPROJECT%
    exit /b 1
)

if not exist "%EDITOR_CMD%" (
    echo [AI4AnimationPy] ERROR: UnrealEditor-Cmd.exe not found at %EDITOR_CMD%
    exit /b 1
)

if not exist "%PY_SCRIPT%" (
    echo [AI4AnimationPy] ERROR: Unreal Python script not found at %PY_SCRIPT%
    exit /b 1
)

if not exist "%AI4A_IMPORT_JSON%" (
    echo [AI4AnimationPy] ERROR: import JSON not found at %AI4A_IMPORT_JSON%
    exit /b 1
)

echo [AI4AnimationPy] Importing Manny test animation into %TARGET_PROJECT% ...
"%EDITOR_CMD%" "%UPROJECT%" -run=pythonscript -script="%PY_SCRIPT%" -unattended -nop4 -nosplash -nullrhi
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Import complete.
exit /b 0
