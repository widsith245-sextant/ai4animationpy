@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "TARGET_PROJECT=%~1"
if "%TARGET_PROJECT%"=="" set "TARGET_PROJECT=D:\PCG_ANIM_RL\NNE_T"

set "UPROJECT=%TARGET_PROJECT%\NNE_T.uproject"
set "EDITOR_CMD=D:\UE_5.5\Engine\Binaries\Win64\UnrealEditor.exe"
set "PY_SCRIPT=%REPO_ROOT%\unreal\Python\retarget_soma_to_manny.py"

set "AI4A_SOMA_SOURCE_MESH=/Game/AI4Animation/SOMA/SOMA_TestAnimation_Output1"
if "%AI4A_SOMA_SOURCE_ANIM%"=="" set "AI4A_SOMA_SOURCE_ANIM=/Game/AI4Animation/SOMA/SOMA_TestAnimation_Output1_Anim"
if "%AI4A_SOMA_SOURCE_IKRIG%"=="" set "AI4A_SOMA_SOURCE_IKRIG=/Game/AI4Animation/SOMA/IK_SOMA_TestAnimation_Output1"
if "%AI4A_SOMA_MANNY_RETARGETER%"=="" set "AI4A_SOMA_MANNY_RETARGETER=/Game/AI4Animation/SOMA/RTG_SOMA_To_Manny"
if "%AI4A_SOMA_TARGET_ANIM%"=="" set "AI4A_SOMA_TARGET_ANIM=/Game/AI4Animation/TestAnimations/AN_TestAnimation_Output1_SOMA_Manny"
if "%AI4A_MANNY_TARGET_MESH%"=="" set "AI4A_MANNY_TARGET_MESH=/Game/Characters/Mannequins/Meshes/SKM_Manny"
if "%AI4A_MANNY_TARGET_IKRIG%"=="" set "AI4A_MANNY_TARGET_IKRIG=/Game/Characters/Mannequins/Rigs/IK_Mannequin"

if not exist "%UPROJECT%" (
    echo [AI4AnimationPy] ERROR: Unreal project not found at %UPROJECT%
    exit /b 1
)

if not exist "%EDITOR_CMD%" (
    echo [AI4AnimationPy] ERROR: UnrealEditor.exe not found at %EDITOR_CMD%
    exit /b 1
)

if not exist "%PY_SCRIPT%" (
    echo [AI4AnimationPy] ERROR: Unreal Python script not found at %PY_SCRIPT%
    exit /b 1
)

echo [AI4AnimationPy] Retargeting SOMA source animation to Manny in %TARGET_PROJECT% ...
"%EDITOR_CMD%" "%UPROJECT%" -ExecutePythonScript="%PY_SCRIPT%" -unattended -nop4 -nosplash -log
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Retarget complete.
exit /b 0
