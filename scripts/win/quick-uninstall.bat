@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "AIFLOW_KIT_ROOT=%~dp0..\.."
for %%I in ("%AIFLOW_KIT_ROOT%") do set "AIFLOW_KIT_ROOT=%%~fI"
set "AIFLOW_DRY_RUN=0"
set "AIFLOW_ASSUME_YES=0"
set "AIFLOW_KEEP_TOOLS=0"
set "AIFLOW_KEEP_ENV=0"

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--dry-run" (
  set "AIFLOW_DRY_RUN=1"
  shift
  goto parse_args
)
if /i "%~1"=="--yes" (
  set "AIFLOW_ASSUME_YES=1"
  shift
  goto parse_args
)
if /i "%~1"=="-y" (
  set "AIFLOW_ASSUME_YES=1"
  shift
  goto parse_args
)
if /i "%~1"=="--keep-tools" (
  set "AIFLOW_KEEP_TOOLS=1"
  shift
  goto parse_args
)
if /i "%~1"=="--keep-env" (
  set "AIFLOW_KEEP_ENV=1"
  shift
  goto parse_args
)
if /i "%~1"=="--help" goto usage
if /i "%~1"=="-h" goto usage
echo Unknown option: %~1
goto usage

:args_done
echo Uninstalling aiflow-kit artifacts from: %AIFLOW_KIT_ROOT%
echo.
echo This removes bundled aiflow skills from:
echo   %USERPROFILE%\.agents\skills
echo   %USERPROFILE%\.claude\skills
echo and generated plugin packages from:
echo   %AIFLOW_KIT_ROOT%\.aiflow\dist\claude
echo   %AIFLOW_KIT_ROOT%\.aiflow\dist\codex
if "%AIFLOW_KEEP_TOOLS%"=="0" (
  echo and shared frontend tools from:
  echo   %AIFLOW_KIT_ROOT%\.tools\frontend-tools
  echo   %AIFLOW_KIT_ROOT%\.tools\ms-playwright
)
if "%AIFLOW_KEEP_ENV%"=="0" (
  echo and local environment config:
  echo   %AIFLOW_KIT_ROOT%\.aiflow\env.local.toml
)
echo.

if "%AIFLOW_DRY_RUN%"=="1" goto run_uninstall
if "%AIFLOW_ASSUME_YES%"=="1" goto run_uninstall
choice /C YN /N /M "Continue quick uninstall? [Y/N] "
if errorlevel 2 goto cancelled

:run_uninstall
set "AIFLOW_SKILLS_SOURCE=%AIFLOW_KIT_ROOT%\packages\aiflow-cli\src\aiflow\assets\skills"
if not exist "%AIFLOW_SKILLS_SOURCE%" (
  echo Bundled skills source not found: %AIFLOW_SKILLS_SOURCE%
  exit /b 1
)

echo [1/4] Remove bundled Codex user skills...
call :remove_skills "%USERPROFILE%\.agents\skills"
if errorlevel 1 exit /b 1

echo.
echo [2/4] Remove bundled Claude Code user skills...
call :remove_skills "%USERPROFILE%\.claude\skills"
if errorlevel 1 exit /b 1

echo.
echo [3/4] Remove generated plugin packages...
call :remove_path "%AIFLOW_KIT_ROOT%\.aiflow\dist\claude"
if errorlevel 1 exit /b 1
call :remove_path "%AIFLOW_KIT_ROOT%\.aiflow\dist\codex"
if errorlevel 1 exit /b 1

echo.
echo [4/4] Remove local runtime artifacts...
if "%AIFLOW_KEEP_TOOLS%"=="0" (
  call :remove_path "%AIFLOW_KIT_ROOT%\.tools\frontend-tools"
  if errorlevel 1 exit /b 1
  call :remove_path "%AIFLOW_KIT_ROOT%\.tools\ms-playwright"
  if errorlevel 1 exit /b 1
) else (
  echo kept tools: %AIFLOW_KIT_ROOT%\.tools\frontend-tools
  echo kept tools: %AIFLOW_KIT_ROOT%\.tools\ms-playwright
)
if "%AIFLOW_KEEP_ENV%"=="0" (
  call :remove_path "%AIFLOW_KIT_ROOT%\.aiflow\env.local.toml"
  if errorlevel 1 exit /b 1
) else (
  echo kept env: %AIFLOW_KIT_ROOT%\.aiflow\env.local.toml
)

echo.
if "%AIFLOW_DRY_RUN%"=="1" (
  echo Quick uninstall dry run complete.
) else (
  echo Quick uninstall complete.
)
exit /b 0

:remove_skills
set "AIFLOW_TARGET_SKILLS=%~1"
if not exist "%AIFLOW_TARGET_SKILLS%" (
  echo missing: %AIFLOW_TARGET_SKILLS%
  exit /b 0
)
for /D %%S in ("%AIFLOW_SKILLS_SOURCE%\*") do (
  call :remove_path "%AIFLOW_TARGET_SKILLS%\%%~nxS"
  if errorlevel 1 exit /b 1
)
exit /b 0

:remove_path
set "AIFLOW_REMOVE_PATH=%~1"
if not exist "%AIFLOW_REMOVE_PATH%" (
  echo missing: %AIFLOW_REMOVE_PATH%
  exit /b 0
)
if "%AIFLOW_DRY_RUN%"=="1" (
  echo would remove: %AIFLOW_REMOVE_PATH%
  exit /b 0
)
if exist "%AIFLOW_REMOVE_PATH%\" (
  rmdir /S /Q "%AIFLOW_REMOVE_PATH%"
) else (
  del /F /Q "%AIFLOW_REMOVE_PATH%"
)
if exist "%AIFLOW_REMOVE_PATH%" (
  echo failed to remove: %AIFLOW_REMOVE_PATH%
  exit /b 1
)
echo removed: %AIFLOW_REMOVE_PATH%
exit /b 0

:cancelled
echo Quick uninstall cancelled.
exit /b 0

:usage
echo Usage: scripts\win\quick-uninstall.bat [--yes] [--dry-run] [--keep-tools] [--keep-env]
echo.
echo Options:
echo   --yes, -y      Skip confirmation prompt.
echo   --dry-run      Print what would be removed without deleting files.
echo   --keep-tools   Keep .tools\frontend-tools and .tools\ms-playwright.
echo   --keep-env     Keep .aiflow\env.local.toml.
exit /b 2
