@echo off
set "AIFLOW_KIT_ROOT=%~dp0.."
for %%I in ("%AIFLOW_KIT_ROOT%") do set "AIFLOW_KIT_ROOT=%%~fI"

set "AIFLOW_PYTHON=%AIFLOW_KIT_ROOT%\.venv\Scripts\python.exe"
if not exist "%AIFLOW_PYTHON%" set "AIFLOW_PYTHON=python"

if defined PYTHONPATH (
    set "PYTHONPATH=%AIFLOW_KIT_ROOT%\packages\aiflow-cli\src;%PYTHONPATH%"
) else (
    set "PYTHONPATH=%AIFLOW_KIT_ROOT%\packages\aiflow-cli\src"
)

"%AIFLOW_PYTHON%" -m aiflow %*
