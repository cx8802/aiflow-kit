@echo off
set "AIFLOW_KIT_ROOT=%~dp0.."
for %%I in ("%AIFLOW_KIT_ROOT%") do set "AIFLOW_KIT_ROOT=%%~fI"

echo Updating aiflow-kit from: %AIFLOW_KIT_ROOT%
echo Target project: %CD%
echo.

echo [1/7] Update Codex user-level aiflow skills...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target codex-user --confirm-global --allow-global --force
if errorlevel 1 goto failed

echo.
echo [2/7] Update Claude Code user-level aiflow skills...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target claude-user --confirm-global --allow-global --force
if errorlevel 1 goto failed

echo.
echo [3/7] Regenerate Claude Code plugin package...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target claude-plugin --output "%AIFLOW_KIT_ROOT%\.aiflow\dist\claude" --force
if errorlevel 1 goto failed

echo.
echo [4/7] Regenerate Codex plugin package...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target codex-plugin --output "%AIFLOW_KIT_ROOT%\.aiflow\dist\codex" --force
if errorlevel 1 goto failed

echo.
echo [5/7] Ensure project aiflow files exist...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" init
if errorlevel 1 goto failed

echo.
echo [6/7] Update project-level skills...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target codex-repo --force
if errorlevel 1 goto failed

echo.
echo [7/7] Refresh project context...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" context
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
echo Restart Codex or Claude Code if you need them to reload global skills/plugins.
exit /b 0

:failed
echo.
echo aiflow-kit update failed.
exit /b 1
