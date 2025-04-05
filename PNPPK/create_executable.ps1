# Stop script execution on first error
$ErrorActionPreference = "Stop"

# Define the output name
$APP_NAME = "gas_flow_regulator"

# Define paths
$MAIN_SCRIPT = ".\main.py"
$DIST_DIR = ".\dist"
$BUILD_DIR = ".\build"

# Set QT_PLUGIN_PATH environment variable (if you need to correctly do it, change the path with yours)
$env:QT_PLUGIN_PATH = ".\venv\Lib\site-packages\PyQt5\Qt5\plugins"

# Clean previous builds
Write-Host "Cleaning previous builds..."
if (Test-Path $DIST_DIR) { Remove-Item -Recurse -Force $DIST_DIR }
if (Test-Path $BUILD_DIR) { Remove-Item -Recurse -Force $BUILD_DIR }

# Create executable with PyInstaller directly from python
# Recommended to use venv if you have problems with PyQt5 like this with encoding: https://github.com/pyinstaller/pyinstaller/issues/7385
# Steps to resolve:
# 1. Create venv: python -m venv venv
# 2. Activate venv: .\venv\Scripts\Activate.ps1
# 3. Install dependencies: pip install -r requirements.txt
# 4. Install PyInstaller: pip install PyInstaller
# 5. Run script: .\create_executable.ps1
Write-Host "Building executable..."
python -m PyInstaller --noconfirm `
					  --onefile `
					  --windowed `
					  --clean `
				      --log-level "INFO" `
					  --name $APP_NAME `
					  --add-data ".;.\" `
					  --add-data "config;config\" `
					  --paths "." `
					  $MAIN_SCRIPT

# Removing build directory and writing message
Remove-Item -Recurse -Force $BUILD_DIR
Write-Host "Build completed. Executable is in $DIST_DIR\$APP_NAME"
