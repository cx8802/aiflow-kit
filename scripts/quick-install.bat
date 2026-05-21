@echo off
set "AIFLOW_KIT_ROOT=%~dp0.."
for %%I in ("%AIFLOW_KIT_ROOT%") do set "AIFLOW_KIT_ROOT=%%~fI"

echo Installing aiflow-kit from: %AIFLOW_KIT_ROOT%
echo.

echo [1/4] Install generic aiflow skills to Codex user skills...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target codex-user --confirm-global --allow-global --force
if errorlevel 1 goto failed

echo.
echo [2/5] Install generic aiflow skills to Claude Code user skills...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target claude-user --confirm-global --allow-global --force
if errorlevel 1 goto failed

echo.
echo [3/5] Generate Claude Code plugin package...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target claude-plugin --output "%AIFLOW_KIT_ROOT%\.aiflow\dist\claude" --force
if errorlevel 1 goto failed

echo.
echo [4/5] Generate Codex plugin package...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" install-skills --target codex-plugin --output "%AIFLOW_KIT_ROOT%\.aiflow\dist\codex" --force
if errorlevel 1 goto failed

echo.
echo [5/5] Verify CLI wrapper...
call "%AIFLOW_KIT_ROOT%\scripts\aiflow-dev.bat" --version
if errorlevel 1 goto failed

echo.
echo Quick install complete.
echo.
echo Codex user skills:
echo   %USERPROFILE%\.agents\skills
echo.
echo Claude Code user skills:
echo   %USERPROFILE%\.claude\skills
echo.
echo Claude plugin package:
echo   %AIFLOW_KIT_ROOT%\.aiflow\dist\claude
echo.
echo Codex plugin package:
echo   %AIFLOW_KIT_ROOT%\.aiflow\dist\codex
echo.
echo Optional current-session PATH:
echo   set PATH=%AIFLOW_KIT_ROOT%\scripts;%%PATH%%
echo.
echo For Claude Code local test:
echo   claude --plugin-dir "%AIFLOW_KIT_ROOT%\.aiflow\dist\claude"
exit /b 0

:failed
echo.
echo Quick install failed.
exit /b 1
