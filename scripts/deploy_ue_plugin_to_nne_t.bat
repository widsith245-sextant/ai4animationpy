@echo off
setlocal

set "REPO_ROOT=%~dp0.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "TARGET_PROJECT=%~1"
if "%TARGET_PROJECT%"=="" set "TARGET_PROJECT=D:\PCG_ANIM_RL\NNE_T"

set "SOURCE_PLUGIN=%REPO_ROOT%\unreal\AI4AnimationNNE"
set "TARGET_PLUGIN=%TARGET_PROJECT%\Plugins\AI4AnimationNNE"
set "ARTIFACTS_ROOT=%REPO_ROOT%\Artifacts\UE"
set "UPROJECT=%TARGET_PROJECT%\NNE_T.uproject"
set "DEFAULT_PACKAGE=geno-biped-locomotion"

if not exist "%UPROJECT%" (
    echo [AI4AnimationPy] ERROR: target Unreal project was not found: %UPROJECT%
    exit /b 1
)

echo [AI4AnimationPy] Deploying plugin source to %TARGET_PLUGIN% ...
robocopy "%SOURCE_PLUGIN%" "%TARGET_PLUGIN%" /MIR /XD Binaries Intermediate .vs >nul
set "ROBOCOPY_EXIT=%errorlevel%"
if %ROBOCOPY_EXIT% GEQ 8 exit /b %ROBOCOPY_EXIT%

if exist "%ARTIFACTS_ROOT%" (
    echo [AI4AnimationPy] Copying exported model packages...
    robocopy "%ARTIFACTS_ROOT%" "%TARGET_PLUGIN%\Resources\ModelPackages" /E >nul
    set "ROBOCOPY_EXIT=%errorlevel%"
    if %ROBOCOPY_EXIT% GEQ 8 exit /b %ROBOCOPY_EXIT%
)

echo [AI4AnimationPy] Enabling AI4AnimationNNE plugin in project descriptor...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$path = '%UPROJECT%';" ^
  "$json = Get-Content -Raw $path | ConvertFrom-Json;" ^
  "if (-not $json.Plugins) { $json | Add-Member -MemberType NoteProperty -Name Plugins -Value @(); };" ^
  "$existing = $json.Plugins | Where-Object { $_.Name -eq 'AI4AnimationNNE' };" ^
  "if (-not $existing) { $json.Plugins += [pscustomobject]@{ Name='AI4AnimationNNE'; Enabled=$true }; } else { $existing.Enabled = $true; };" ^
  "$json | ConvertTo-Json -Depth 100 | Set-Content -Encoding UTF8 $path"
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Writing default plugin settings...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$configPath = Join-Path '%TARGET_PROJECT%' 'Config\DefaultGame.ini';" ^
  "$payload = @() + '' + '[/Script/AI4AnimationNNE.AI4AnimationNNEProjectSettings]' + 'bPreferPluginResourceDirectory=True' + 'RelativeModelPackageRoot=Resources/ModelPackages' + 'DefaultPackageName=%DEFAULT_PACKAGE%' + 'DefaultRuntimeName=NNERuntimeORTCpu' + 'bLoadDefaultPackageOnInitialize=False';" ^
  "$existing = if (Test-Path $configPath) { Get-Content -Raw $configPath } else { '' };" ^
  "$pattern = '(?ms)^\[/Script/AI4AnimationNNE\.AI4AnimationNNEProjectSettings\].*?(?=^\[|\z)';" ^
  "$replacement = ($payload -join [Environment]::NewLine) + [Environment]::NewLine;" ^
  "if ($existing -match $pattern) { $updated = [regex]::Replace($existing, $pattern, $replacement); } else { $updated = $existing.TrimEnd() + [Environment]::NewLine + [Environment]::NewLine + $replacement; };" ^
  "Set-Content -Path $configPath -Value $updated -Encoding UTF8"
if errorlevel 1 exit /b 1

echo [AI4AnimationPy] Plugin deployment finished.
exit /b 0
