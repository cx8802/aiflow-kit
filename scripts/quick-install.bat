@echo off
set "AIFLOW_KIT_ROOT=%~dp0.."
for %%I in ("%AIFLOW_KIT_ROOT%") do set "AIFLOW_KIT_ROOT=%%~fI"
set "AIFLOW_INSTALL_GLOBAL=0"

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--global-skills" (
  set "AIFLOW_INSTALL_GLOBAL=1"
  shift
  goto parse_args
)
if /i "%~1"=="--help" goto usage
if /i "%~1"=="-h" goto usage
echo Unknown option: %~1
goto usage

:args_done

echo Installing aiflow-kit from: %AIFLOW_KIT_ROOT%
if "%AIFLOW_INSTALL_GLOBAL%"=="1" (
  echo User-level skills: enabled by --global-skills.
) else (
  echo User-level skills: skipped. Use --global-skills for explicit global install.
)
echo.

echo [1/8] Ensure project virtual environment and editable CLI package...
if not exist "%AIFLOW_KIT_ROOT%\.venv\Scripts\python.exe" (
  python -m venv "%AIFLOW_KIT_ROOT%\.venv"
  if errorlevel 1 goto failed
)
call "%AIFLOW_KIT_ROOT%\scripts\use-project-env.bat" quiet
"%AIFLOW_KIT_ROOT%\.venv\Scripts\python.exe" -m pip install -e "%AIFLOW_KIT_ROOT%\packages\aiflow-cli"
if errorlevel 1 goto failed

echo.
echo [2/8] Detect local aiflow-kit path and tool environment...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" env detect
if errorlevel 1 goto failed

echo.
echo [3/8] Install shared aiflow-kit frontend design and Playwright tooling...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" frontend install
if errorlevel 1 goto failed

echo.
echo [4/8] Install bundled aiflow skills to this repository...
pushd "%AIFLOW_KIT_ROOT%"
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target codex-repo --force
set "AIFLOW_LAST_ERROR=%ERRORLEVEL%"
popd
if not "%AIFLOW_LAST_ERROR%"=="0" goto failed

echo.
echo [5/8] Generate Claude Code plugin package...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target claude-plugin --output "%AIFLOW_KIT_ROOT%\.aiflow\dist\claude" --force
if errorlevel 1 goto failed

echo.
echo [6/8] Generate Codex plugin package...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target codex-plugin --output "%AIFLOW_KIT_ROOT%\.aiflow\dist\codex" --force
if errorlevel 1 goto failed

echo.
if not "%AIFLOW_INSTALL_GLOBAL%"=="1" goto skip_global_skills
echo [7/8] Install generic aiflow skills to user-level Codex and Claude Code...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target codex-user --confirm-global --allow-global --force
if errorlevel 1 goto failed
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target claude-user --confirm-global --allow-global --force
if errorlevel 1 goto failed
goto after_global_skills

:skip_global_skills
echo [7/8] Skip user-level skills. Use --global-skills for explicit global install.

:after_global_skills

echo.
echo [8/8] Verify CLI wrapper...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" --version
if errorlevel 1 goto failed

echo.
echo Quick install complete.
echo.
echo Project-local Python CLI:
echo   %AIFLOW_KIT_ROOT%\.venv
echo.
echo Project skills:
echo   %AIFLOW_KIT_ROOT%\.agents\skills
echo.
echo Claude plugin package:
echo   %AIFLOW_KIT_ROOT%\.aiflow\dist\claude
echo.
echo Codex plugin package:
echo   %AIFLOW_KIT_ROOT%\.aiflow\dist\codex
echo.
echo Local environment config:
echo   %AIFLOW_KIT_ROOT%\.aiflow\env.local.toml
echo.
echo Shared aiflow-kit frontend tools:
echo   %AIFLOW_KIT_ROOT%\.tools\frontend-tools
echo   %AIFLOW_KIT_ROOT%\.tools\ms-playwright
echo.
echo Optional current-session PATH:
echo   set PATH=%AIFLOW_KIT_ROOT%\scripts;%%PATH%%
echo.
echo For Claude Code local test:
echo   claude --plugin-dir "%AIFLOW_KIT_ROOT%\.aiflow\dist\claude"
exit /b 0

:usage
echo Usage: %~nx0 [--global-skills]
echo.
echo   Default: install the aiflow CLI and bundled skills into this repository only.
echo   --global-skills  Also install generic skills to Codex and Claude user-level directories.
exit /b 2

:failed
echo.
echo Quick install failed.
exit /b 1
