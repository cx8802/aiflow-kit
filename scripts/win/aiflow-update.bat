@echo off
set "AIFLOW_KIT_ROOT=%~dp0..\.."
for %%I in ("%AIFLOW_KIT_ROOT%") do set "AIFLOW_KIT_ROOT=%%~fI"
set "AIFLOW_UPDATE_PROJECT=0"
set "AIFLOW_UPDATE_GLOBAL=0"

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--with-project" (
  set "AIFLOW_UPDATE_PROJECT=1"
  shift
  goto parse_args
)
if /i "%~1"=="--project" (
  set "AIFLOW_UPDATE_PROJECT=1"
  shift
  goto parse_args
)
if /i "%~1"=="--global-skills" (
  set "AIFLOW_UPDATE_GLOBAL=1"
  shift
  goto parse_args
)
if /i "%~1"=="--help" goto usage
if /i "%~1"=="-h" goto usage
echo Unknown option: %~1
goto usage

:args_done

echo Updating aiflow-kit from: %AIFLOW_KIT_ROOT%
if "%AIFLOW_UPDATE_PROJECT%"=="1" (
  echo Target project: %CD%
) else (
  echo Target project: skipped. Use --with-project to update project aiflow files.
)
if "%AIFLOW_UPDATE_GLOBAL%"=="1" (
  echo User-level skills: enabled by --global-skills.
) else (
  echo User-level skills: skipped. Use --global-skills for explicit global update.
)
echo.

echo [1/11] Ensure project virtual environment and editable CLI package...
if not exist "%AIFLOW_KIT_ROOT%\.venv\Scripts\python.exe" (
  python -m venv "%AIFLOW_KIT_ROOT%\.venv"
  if errorlevel 1 goto failed
)
call "%AIFLOW_KIT_ROOT%\scripts\win\use-project-env.bat" quiet
"%AIFLOW_KIT_ROOT%\.venv\Scripts\python.exe" -m pip install -e "%AIFLOW_KIT_ROOT%\packages\aiflow-cli"
if errorlevel 1 goto failed

echo.
echo [2/11] Detect local aiflow-kit path and tool environment...
call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" env detect
if errorlevel 1 goto failed

echo.
echo [3/11] Install shared aiflow-kit frontend design and Playwright tooling...
call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" frontend install
if errorlevel 1 goto failed

echo.
echo [4/11] Update aiflow-kit project-level skills...
pushd "%AIFLOW_KIT_ROOT%"
call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" install-skills --target codex-repo --force
set "AIFLOW_LAST_ERROR=%ERRORLEVEL%"
popd
if not "%AIFLOW_LAST_ERROR%"=="0" goto failed

echo.
echo [5/11] Regenerate Claude Code plugin package...
call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" install-skills --target claude-plugin --output "%AIFLOW_KIT_ROOT%\.aiflow\dist\claude" --force
if errorlevel 1 goto failed

echo.
echo [6/11] Regenerate Codex plugin package...
call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" install-skills --target codex-plugin --output "%AIFLOW_KIT_ROOT%\.aiflow\dist\codex" --force
if errorlevel 1 goto failed

echo.
if not "%AIFLOW_UPDATE_GLOBAL%"=="1" goto skip_global
echo [7/11] Update Codex user-level aiflow skills...
call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" install-skills --target codex-user --confirm-global --allow-global --force
if errorlevel 1 goto failed

echo.
echo [8/11] Update Claude Code user-level aiflow skills...
call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" install-skills --target claude-user --confirm-global --allow-global --force
if errorlevel 1 goto failed
goto after_global

:skip_global
echo [7/11] Skip Codex user-level aiflow skills.
echo [8/11] Skip Claude Code user-level aiflow skills.

:after_global

echo.
if not "%AIFLOW_UPDATE_PROJECT%"=="1" goto skip_project

echo [9/11] Ensure project aiflow files exist...
call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" init
if errorlevel 1 goto failed

echo.
echo [10/11] Update project-level skills...
call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" install-skills --target codex-repo --force
if errorlevel 1 goto failed

echo.
echo [11/11] Refresh project context and compact context...
call "%AIFLOW_KIT_ROOT%\scripts\win\aiflow-dev.bat" context --compact
if errorlevel 1 goto failed
goto done_project

:skip_project
echo.
echo [9/11] Skip project aiflow files. Use --with-project to install or refresh them.
echo [10/11] Skip project-level skills.
echo [11/11] Skip project context refresh.

:done_project

echo.
echo aiflow-kit update complete.
echo.
echo Updated project-local Python CLI:
echo   %AIFLOW_KIT_ROOT%\.venv
echo.
echo Updated aiflow-kit project skills:
echo   %AIFLOW_KIT_ROOT%\.agents\skills
echo.
if "%AIFLOW_UPDATE_PROJECT%"=="1" (
  echo Updated project skills:
  echo   %CD%\.agents\skills
  echo.
)
if "%AIFLOW_UPDATE_GLOBAL%"=="1" (
  echo Updated global Codex skills:
  echo   %USERPROFILE%\.agents\skills
  echo.
  echo Updated global Claude Code skills:
  echo   %USERPROFILE%\.claude\skills
  echo.
)
echo Updated Claude plugin package:
echo   %AIFLOW_KIT_ROOT%\.aiflow\dist\claude
echo.
echo Updated local environment config:
echo   %AIFLOW_KIT_ROOT%\.aiflow\env.local.toml
echo.
echo Updated shared aiflow-kit frontend tools:
echo   %AIFLOW_KIT_ROOT%\.tools\frontend-tools
echo   %AIFLOW_KIT_ROOT%\.tools\ms-playwright
echo.
if "%AIFLOW_UPDATE_GLOBAL%"=="1" echo Restart Codex or Claude Code if you need them to reload global skills/plugins.
exit /b 0

:usage
echo Usage: %~nx0 [--with-project] [--global-skills]
echo.
echo   Default: update the aiflow-kit project-local environment only.
echo   --with-project   Also create or refresh aiflow files in the current project.
echo   --global-skills  Also update Codex and Claude user-level skills.
exit /b 2

:failed
echo.
echo aiflow-kit update failed.
exit /b 1
