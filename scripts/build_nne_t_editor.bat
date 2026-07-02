@echo off
setlocal

set "TARGET_PROJECT=%~1"
if "%TARGET_PROJECT%"=="" set "TARGET_PROJECT=D:\PCG_ANIM_RL\NNE_T"
set "UPROJECT=%TARGET_PROJECT%\NNE_T.uproject"
set "BUILD_BAT=D:\UE_5.5\Engine\Build\BatchFiles\Build.bat"

if not exist "%BUILD_BAT%" (
    echo [AI4AnimationPy] ERROR: Unreal Build.bat not found at %BUILD_BAT%
    exit /b 1
)

if not exist "%UPROJECT%" (
    echo [AI4AnimationPy] ERROR: Unreal project not found at %UPROJECT%
    exit /b 1
)

echo [AI4AnimationPy] Building NNE_TEditor with deployed plugin...
call "%BUILD_BAT%" NNE_TEditor Win64 Development "%UPROJECT%" -WaitMutex -FromMsBuild
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Build complete.
exit /b 0
