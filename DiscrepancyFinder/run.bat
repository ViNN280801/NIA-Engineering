@echo off
setlocal enabledelayedexpansion

:: Variables
set "pythonVersion=3.12"
set "pythonInstallerUrl=https://www.python.org/ftp/python/%pythonVersion%.0/python-%pythonVersion%.0-amd64.exe"
set "installerPath=%TEMP%\python-installer.exe"

:: Function to check Python version
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "installedVersion=%%v"
if defined installedVersion (
    for /f "tokens=1,2 delims=." %%a in ("!installedVersion!") do (
        set "major=%%a"
        set "minor=%%b"
    )
    if "!major!.!minor!"=="%pythonVersion%" goto RunApplication
)

:: Python not found - Install Python
echo Python %pythonVersion% not found. Installing...
powershell -Command "Invoke-WebRequest -Uri '%pythonInstallerUrl%' -OutFile '%installerPath%'"
start /wait "" "%installerPath%" /quiet InstallAllUsers=1 PrependPath=1
del "%installerPath%"

:: Verify Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo Python installation failed.
    exit /b 1
)

:: Run Application
:RunApplication
echo Running the application...
python main.py
pause
