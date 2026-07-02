@echo off
setlocal

set "TARGET_PROJECT=%~1"
if "%TARGET_PROJECT%"=="" set "TARGET_PROJECT=D:\PCG_ANIM_RL\NNE_T"

call "%~dp0bootstrap_env.bat"
if errorlevel 1 exit /b 1

call "%~dp0export_ue_bundle.bat"
if errorlevel 1 exit /b 1

call "%~dp0deploy_ue_plugin_to_nne_t.bat" "%TARGET_PROJECT%"
if errorlevel 1 exit /b 1

call "%~dp0build_nne_t_editor.bat" "%TARGET_PROJECT%"
if errorlevel 1 exit /b 1

call "%~dp0open_nne_t_editor.bat" "%TARGET_PROJECT%"
if errorlevel 1 exit /b 1

exit /b 0
