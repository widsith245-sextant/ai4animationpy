@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"
set "VERIFY_SCRIPT=%REPO_ROOT%\scripts\verify_soma_test_animation_contract.py"

if not exist "%PYTHON_EXE%" (
    echo [AI4AnimationPy] ERROR: Python environment not found at %PYTHON_EXE%
    exit /b 1
)

if not exist "%VERIFY_SCRIPT%" (
    echo [AI4AnimationPy] ERROR: Verification script not found at %VERIFY_SCRIPT%
    exit /b 1
)

echo [AI4AnimationPy] Verifying SOMA NPZ -> UE animation contract...
"%PYTHON_EXE%" "%VERIFY_SCRIPT%"
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Verification complete.
exit /b 0
