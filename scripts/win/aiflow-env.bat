@echo off
set "AIFLOW_KIT=%~dp0..\.."
for %%I in ("%AIFLOW_KIT%") do set "AIFLOW_KIT=%%~fI"
set "AIFLOW_KIT_ROOT=%AIFLOW_KIT%"
set "PATH=%AIFLOW_KIT%\scripts\win;%PATH%"

echo aiflow current CMD session is ready.
echo.
echo AIFLOW_KIT=%AIFLOW_KIT%
echo AIFLOW_KIT_ROOT=%AIFLOW_KIT_ROOT%
echo PATH prepended with: %AIFLOW_KIT%\scripts\win
echo.
echo From any project directory, run:
echo   aiflow-install
echo.
echo This script only changes the current CMD session.
