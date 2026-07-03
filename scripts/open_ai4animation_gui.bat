@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    echo [AI4AnimationPy] ERROR: Python environment not found. Run scripts\bootstrap_env.bat first.
    exit /b 1
)

start "" "%PYTHON_EXE%" "%REPO_ROOT%\tools\ai4animation_gui.py"
exit /b 0
