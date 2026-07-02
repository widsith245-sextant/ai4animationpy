@echo off
setlocal enabledelayedexpansion

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"
set "VENV_PYTHON=%REPO_ROOT%\.venv\Scripts\python.exe"

if exist "%VENV_PYTHON%" goto install

echo [AI4AnimationPy] Creating local virtual environment...
py -3.12 -c "import sys" >nul 2>nul
if %errorlevel%==0 (
    py -3.12 -m venv "%REPO_ROOT%\.venv"
    goto install
)

py -3.11 -c "import sys" >nul 2>nul
if %errorlevel%==0 (
    py -3.11 -m venv "%REPO_ROOT%\.venv"
    goto install
)

echo [AI4AnimationPy] ERROR: Python 3.11 or 3.12 was not found through the py launcher.
exit /b 1

:install
if not exist "%VENV_PYTHON%" (
    echo [AI4AnimationPy] ERROR: virtual environment python executable not found.
    exit /b 1
)

echo [AI4AnimationPy] Installing runtime dependencies into %REPO_ROOT%\.venv ...
call "%VENV_PYTHON%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1

call "%VENV_PYTHON%" -m pip install -r "%REPO_ROOT%\requirements\base.txt"
if errorlevel 1 exit /b 1

call "%VENV_PYTHON%" -m pip install -e "%REPO_ROOT%"
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Environment ready.
exit /b 0
