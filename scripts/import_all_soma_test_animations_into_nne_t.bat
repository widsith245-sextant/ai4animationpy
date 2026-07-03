@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "TARGET_PROJECT=%~1"
if "%TARGET_PROJECT%"=="" set "TARGET_PROJECT=D:\PCG_ANIM_RL\NNE_T"

set "JSON_DIR=%~2"
if "%JSON_DIR%"=="" set "JSON_DIR=%REPO_ROOT%\Artifacts\UE\SOMA\BatchJson"

set "UPROJECT=%TARGET_PROJECT%\NNE_T.uproject"
set "EDITOR_CMD=D:\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
set "PY_SCRIPT=%REPO_ROOT%\unreal\Python\import_soma_animation_batch_to_project.py"

set "AI4A_IMPORT_JSON_DIR=%JSON_DIR%"
set "AI4A_IMPORT_DEST=/Game/AI4Animation/SOMA"
set "AI4A_IMPORT_SKELETON=/Game/AI4Animation/SOMA/SOMA_TestAnimation_Output1_Skeleton.SOMA_TestAnimation_Output1_Skeleton"
set "AI4A_IMPORT_PREVIEW_MESH=/Game/AI4Animation/SOMA/SOMA_TestAnimation_Output1.SOMA_TestAnimation_Output1"

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

if not exist "%AI4A_IMPORT_JSON_DIR%" (
    echo [AI4AnimationPy] ERROR: SOMA import JSON directory not found at %AI4A_IMPORT_JSON_DIR%
    exit /b 1
)

echo [AI4AnimationPy] Importing all SOMA test animations into %TARGET_PROJECT% ...
"%EDITOR_CMD%" "%UPROJECT%" -run=pythonscript -script="%PY_SCRIPT%" -unattended -nop4 -nosplash -nullrhi
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Imported all SOMA test animations.
exit /b 0
