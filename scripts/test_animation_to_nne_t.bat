@echo off
setlocal

set "TARGET_PROJECT=%~1"
if "%TARGET_PROJECT%"=="" set "TARGET_PROJECT=D:\PCG_ANIM_RL\NNE_T"

call "%~dp0export_test_animation_to_ue_json.bat"
if errorlevel 1 exit /b 1

call "%~dp0deploy_ue_plugin_to_nne_t.bat" "%TARGET_PROJECT%"
if errorlevel 1 exit /b 1

call "%~dp0build_nne_t_editor.bat" "%TARGET_PROJECT%"
if errorlevel 1 exit /b 1

call "%~dp0import_test_animation_into_nne_t.bat" "%TARGET_PROJECT%"
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Test animation pipeline completed for %TARGET_PROJECT%.
exit /b 0
