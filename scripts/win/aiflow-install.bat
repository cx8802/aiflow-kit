@echo off
setlocal EnableExtensions

set "AIFLOW_KIT_ROOT=%~dp0..\.."
for %%I in ("%AIFLOW_KIT_ROOT%") do set "AIFLOW_KIT_ROOT=%%~fI"
set "AIFLOW_SKIP_RULES=0"
set "AIFLOW_NO_CONTEXT=0"

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--skip-rules" (
  set "AIFLOW_SKIP_RULES=1"
  shift
  goto parse_args
)
if /i "%~1"=="--no-context" (
  set "AIFLOW_NO_CONTEXT=1"
  shift
  goto parse_args
)
if /i "%~1"=="--help" goto usage
if /i "%~1"=="-h" goto usage
echo Unknown option: %~1
goto usage

:args_done
set "AIFLOW_INIT_CONTEXT_ARG="
if "%AIFLOW_NO_CONTEXT%"=="1" set "AIFLOW_INIT_CONTEXT_ARG=--no-context"

echo Installing aiflow into project:
echo   %CD%
echo.
echo Source aiflow-kit:
echo   %AIFLOW_KIT_ROOT%
echo.

if "%AIFLOW_SKIP_RULES%"=="1" (
  echo [1/5] Initialize .aiflow config without AGENTS.md or CLAUDE.md...
  call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" init --no-codex --no-claude %AIFLOW_INIT_CONTEXT_ARG%
) else (
  echo [1/5] Initialize project aiflow files...
  call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" init %AIFLOW_INIT_CONTEXT_ARG%
)
if errorlevel 1 goto failed

echo.
echo [2/5] Install bundled skills to this project...
call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" install-skills
if errorlevel 1 goto failed

echo.
echo [3/5] Detect local environment...
call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" env detect
if errorlevel 1 goto failed

echo.
if "%AIFLOW_NO_CONTEXT%"=="1" (
  echo [4/5] Skip context refresh by request.
) else (
  echo [4/5] Refresh compact context...
  call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" context --compact
  if errorlevel 1 goto failed
)

echo.
echo [5/5] Preview verification commands...
call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" verify --auto --dry-run
if errorlevel 1 goto failed

echo.
echo aiflow project install complete.
echo.
echo Installed project files:
echo   .aiflow\
echo   .agents\skills\
if not "%AIFLOW_SKIP_RULES%"=="1" (
  echo   AGENTS.md or AGENTS.md.new
  echo   CLAUDE.md or CLAUDE.md.new
)
exit /b 0

:usage
echo Usage: aiflow-install [--skip-rules] [--no-context]
echo.
echo   Run this from the target project root.
echo   Default: safely initialize project rules, install project skills, refresh context.
echo   --skip-rules  Do not create AGENTS.md or CLAUDE.md.
echo   --no-context  Skip context generation.
exit /b 2

:failed
echo.
echo aiflow project install failed.
exit /b 1
