@echo off
set "AIFLOW_KIT_ROOT=%~dp0.."
for %%I in ("%AIFLOW_KIT_ROOT%") do set "AIFLOW_KIT_ROOT=%%~fI"

if defined PYTHONPATH (
    set "PYTHONPATH=%AIFLOW_KIT_ROOT%\src;%PYTHONPATH%"
) else (
    set "PYTHONPATH=%AIFLOW_KIT_ROOT%\src"
)

python -m aiflow %*
