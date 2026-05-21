@echo off
set "AIFLOW_KIT_ROOT=%~dp0.."
for %%I in ("%AIFLOW_KIT_ROOT%") do set "AIFLOW_KIT_ROOT=%%~fI"

echo Updating aiflow-kit from: %AIFLOW_KIT_ROOT%
echo Target project: %CD%
echo.

echo [1/9] Detect local aiflow-kit path and tool environment...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" env detect
if errorlevel 1 goto failed

echo.
echo [2/9] Install shared aiflow-kit frontend design and Playwright tooling...
call "%AIFLOW_KIT_ROOT%\scripts\use-project-env.bat" quiet
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" frontend install
if errorlevel 1 goto failed

echo.
echo [3/9] Update Codex user-level aiflow skills...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target codex-user --confirm-global --allow-global --force
if errorlevel 1 goto failed

echo.
echo [4/9] Update Claude Code user-level aiflow skills...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target claude-user --confirm-global --allow-global --force
if errorlevel 1 goto failed

echo.
echo [5/9] Regenerate Claude Code plugin package...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target claude-plugin --output "%AIFLOW_KIT_ROOT%\.aiflow\dist\claude" --force
if errorlevel 1 goto failed

echo.
echo [6/9] Regenerate Codex plugin package...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target codex-plugin --output "%AIFLOW_KIT_ROOT%\.aiflow\dist\codex" --force
if errorlevel 1 goto failed

echo.
echo [7/9] Ensure project aiflow files exist...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" init
if errorlevel 1 goto failed

echo.
echo [8/9] Update project-level skills...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target codex-repo --force
if errorlevel 1 goto failed

echo.
echo [9/9] Refresh project context and compact context...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" context --compact
if errorlevel 1 goto failed

echo.
echo aiflow-kit update complete.
echo.
echo Updated global Codex skills:
echo   %USERPROFILE%\.agents\skills
echo.
echo Updated global Claude Code skills:
echo   %USERPROFILE%\.claude\skills
echo.
echo Updated project skills:
echo   %CD%\.agents\skills
echo.
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
echo Restart Codex or Claude Code if you need them to reload global skills/plugins.
exit /b 0

:failed
echo.
echo aiflow-kit update failed.
exit /b 1
