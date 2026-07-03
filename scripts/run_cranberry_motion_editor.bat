@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"
set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo [AI4AnimationPy] ERROR: Python environment not found at %PYTHON_EXE%
    exit /b 1
)

echo [AI4AnimationPy] Launching Cranberry Motion Editor...
"%PYTHON_EXE%" "%REPO_ROOT%\starter\quickstart\cranberry_motion_editor.py"
exit /b %errorlevel%
