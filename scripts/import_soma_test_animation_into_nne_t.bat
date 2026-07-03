@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "TARGET_PROJECT=%~1"
if "%TARGET_PROJECT%"=="" set "TARGET_PROJECT=D:\PCG_ANIM_RL\NNE_T"

set "UPROJECT=%TARGET_PROJECT%\NNE_T.uproject"
set "EDITOR_CMD=D:\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
set "PY_SCRIPT=%REPO_ROOT%\unreal\Python\import_soma_source_to_project.py"
set "AI4A_SOMA_SOURCE_GLB=%~2"
if "%AI4A_SOMA_SOURCE_GLB%"=="" set "AI4A_SOMA_SOURCE_GLB=%REPO_ROOT%\Artifacts\UE\SOMA\SOMA_TestAnimation_Output1.glb"
set "AI4A_SOMA_IMPORT_DEST=/Game/AI4Animation/SOMA"
set "AI4A_SOMA_CLEAR_DEST=1"

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

if not exist "%AI4A_SOMA_SOURCE_GLB%" (
    echo [AI4AnimationPy] ERROR: SOMA source GLB not found at %AI4A_SOMA_SOURCE_GLB%
    exit /b 1
)

echo [AI4AnimationPy] Importing SOMA source assets into %TARGET_PROJECT% ...
"%EDITOR_CMD%" "%UPROJECT%" -run=pythonscript -script="%PY_SCRIPT%" -unattended -nop4 -nosplash -nullrhi
if errorlevel 1 exit /b 1

call "%~dp0export_soma_test_animation_to_ue_json.bat"
if errorlevel 1 exit /b 1

call "%~dp0import_soma_exact_animation_into_nne_t.bat" "%TARGET_PROJECT%"
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] SOMA source import complete.
exit /b 0
