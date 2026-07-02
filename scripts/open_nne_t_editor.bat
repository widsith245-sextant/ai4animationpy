@echo off
setlocal

set "TARGET_PROJECT=%~1"
if "%TARGET_PROJECT%"=="" set "TARGET_PROJECT=D:\PCG_ANIM_RL\NNE_T"
set "UPROJECT=%TARGET_PROJECT%\NNE_T.uproject"
set "EDITOR_EXE=D:\UE_5.5\Engine\Binaries\Win64\UnrealEditor.exe"

if not exist "%EDITOR_EXE%" (
    echo [AI4AnimationPy] ERROR: UnrealEditor.exe not found at %EDITOR_EXE%
    exit /b 1
)

if not exist "%UPROJECT%" (
    echo [AI4AnimationPy] ERROR: Unreal project not found at %UPROJECT%
    exit /b 1
)

start "" "%EDITOR_EXE%" "%UPROJECT%"
exit /b 0
