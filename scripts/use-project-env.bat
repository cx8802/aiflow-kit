@echo off

set "AIFLOW_SCRIPT_DIR=%~dp0"
set "AIFLOW_ENV_QUIET="
set "AIFLOW_USE_PROXY="

:parse_args
if "%~1"=="" goto args_done
if /I "%~1"=="quiet" set "AIFLOW_ENV_QUIET=1"
if /I "%~1"=="--quiet" set "AIFLOW_ENV_QUIET=1"
if /I "%~1"=="proxy" set "AIFLOW_USE_PROXY=1"
if /I "%~1"=="--proxy" set "AIFLOW_USE_PROXY=1"
shift
goto parse_args
:args_done

set "PROJECT_ROOT=%AIFLOW_SCRIPT_DIR%.."
for %%I in ("%PROJECT_ROOT%") do set "PROJECT_ROOT=%%~fI"

set "CACHE_ROOT=%PROJECT_ROOT%\.cache"
set "TOOLS_ROOT=%PROJECT_ROOT%\.tools"
set "TOOLS_BIN=%TOOLS_ROOT%\bin"
set "NPM_PREFIX=%TOOLS_ROOT%\npm-global"
set "NPM_BIN=%NPM_PREFIX%\node_modules\.bin"
set "PNPM_HOME=%TOOLS_ROOT%\pnpm"
set "MAVEN_USER_HOME=%CACHE_ROOT%\maven-user-home"
set "PLAYWRIGHT_BROWSERS_PATH=%TOOLS_ROOT%\ms-playwright"

for %%D in (
    "%CACHE_ROOT%"
    "%TOOLS_ROOT%"
    "%TOOLS_BIN%"
    "%NPM_PREFIX%"
    "%NPM_BIN%"
    "%PNPM_HOME%"
    "%TOOLS_ROOT%\frontend-tools"
    "%PLAYWRIGHT_BROWSERS_PATH%"
    "%CACHE_ROOT%\go-build"
    "%CACHE_ROOT%\go-mod"
    "%CACHE_ROOT%\npm"
    "%CACHE_ROOT%\pnpm-store"
    "%CACHE_ROOT%\yarn"
    "%CACHE_ROOT%\corepack"
    "%MAVEN_USER_HOME%"
    "%CACHE_ROOT%\maven\repository"
    "%CACHE_ROOT%\java-tmp"
) do (
    if not exist "%%~D" mkdir "%%~D" >nul 2>nul
)

rem Python: use existing project venv when present, without modifying global pyenv.
set "VENV_SCRIPTS=%PROJECT_ROOT%\.venv\Scripts"
if exist "%VENV_SCRIPTS%" (
    set "VIRTUAL_ENV=%PROJECT_ROOT%\.venv"
    set "PATH=%VENV_SCRIPTS%;%PATH%"
)

rem Go: keep module/build caches and installed binaries inside this repository.
set "GOCACHE=%CACHE_ROOT%\go-build"
set "GOMODCACHE=%CACHE_ROOT%\go-mod"
set "GOBIN=%TOOLS_BIN%"
set "GOTOOLCHAIN=local"
set "PATH=%GOBIN%;%PATH%"

rem Node/npm/pnpm/yarn/corepack: avoid user-level global installs and caches.
set "NPM_CONFIG_CACHE=%CACHE_ROOT%\npm"
set "NPM_CONFIG_PREFIX=%NPM_PREFIX%"
set "NPM_CONFIG_USERCONFIG=%PROJECT_ROOT%\.npmrc"
set "PNPM_HOME=%PNPM_HOME%"
set "PNPM_STORE_DIR=%CACHE_ROOT%\pnpm-store"
set "COREPACK_HOME=%CACHE_ROOT%\corepack"
set "YARN_CACHE_FOLDER=%CACHE_ROOT%\yarn"
set "PATH=%NPM_BIN%;%PNPM_HOME%;%PATH%"

rem Java/Maven: use existing JDK/Maven binaries, but keep Maven home/repository local.
set "AIFLOW_JAVA_EXE="
for /f "delims=" %%J in ('where java.exe 2^>nul') do (
    if not defined AIFLOW_JAVA_EXE set "AIFLOW_JAVA_EXE=%%J"
)
if not defined AIFLOW_JAVA_EXE goto after_java_home
for %%J in ("%AIFLOW_JAVA_EXE%") do set "AIFLOW_JAVA_BIN=%%~dpJ"
for %%J in ("%AIFLOW_JAVA_BIN%..") do set "JAVA_HOME=%%~fJ"
:after_java_home
set "MAVEN_OPTS=-Djava.io.tmpdir=%CACHE_ROOT%\java-tmp"

set "AIFLOW_PROJECT_ROOT=%PROJECT_ROOT%"

rem Optional network proxy for the current cmd session only.
if not defined AIFLOW_PROXY_URL set "AIFLOW_PROXY_URL=http://127.0.0.1:10808"
if defined AIFLOW_USE_PROXY (
    set "HTTP_PROXY=%AIFLOW_PROXY_URL%"
    set "HTTPS_PROXY=%AIFLOW_PROXY_URL%"
    set "ALL_PROXY=%AIFLOW_PROXY_URL%"
    set "http_proxy=%AIFLOW_PROXY_URL%"
    set "https_proxy=%AIFLOW_PROXY_URL%"
    set "all_proxy=%AIFLOW_PROXY_URL%"
    set "NO_PROXY=localhost,127.0.0.1,::1"
    set "no_proxy=localhost,127.0.0.1,::1"
    set "MAVEN_OPTS=%MAVEN_OPTS% -Dhttp.proxyHost=127.0.0.1 -Dhttp.proxyPort=10808 -Dhttps.proxyHost=127.0.0.1 -Dhttps.proxyPort=10808"
)

if not defined AIFLOW_ENV_QUIET (
    echo Project environment activated for: %PROJECT_ROOT%
    echo Caches: %CACHE_ROOT%
    echo Tools:  %TOOLS_ROOT%
    echo.
    echo Key environment variables:
    echo   VIRTUAL_ENV=%VIRTUAL_ENV%
    echo   GOCACHE=%GOCACHE%
    echo   GOMODCACHE=%GOMODCACHE%
    echo   GOBIN=%GOBIN%
    echo   NPM_CONFIG_CACHE=%NPM_CONFIG_CACHE%
    echo   NPM_CONFIG_PREFIX=%NPM_CONFIG_PREFIX%
    echo   PNPM_HOME=%PNPM_HOME%
    echo   PLAYWRIGHT_BROWSERS_PATH=%PLAYWRIGHT_BROWSERS_PATH%
    echo   MAVEN_USER_HOME=%MAVEN_USER_HOME%
    echo   JAVA_HOME=%JAVA_HOME%
    if defined AIFLOW_USE_PROXY (
        echo   HTTP_PROXY=%HTTP_PROXY%
        echo   HTTPS_PROXY=%HTTPS_PROXY%
        echo   NO_PROXY=%NO_PROXY%
    )
)
