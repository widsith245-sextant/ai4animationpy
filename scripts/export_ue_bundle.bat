@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"
set "VENV_PYTHON=%REPO_ROOT%\.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    call "%REPO_ROOT%\scripts\bootstrap_env.bat"
    if errorlevel 1 exit /b 1
)

echo [AI4AnimationPy] Exporting UE/NNE package...
call "%VENV_PYTHON%" "%REPO_ROOT%\starter\quickstart\export_ue_nne_bundle.py"
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] UE/NNE package export complete.
exit /b 0
