# Stop script execution on first error
$ErrorActionPreference = "Stop"

# Define the output name
$APP_NAME = "gas_flow_regulator"

# Define paths
$MAIN_SCRIPT = ".\main.py"
$DIST_DIR = ".\dist"
$BUILD_DIR = ".\build"

# Set QT_PLUGIN_PATH environment variable (if you need to correctly do it, change the path with yours)
# $env:QT_PLUGIN_PATH = ".\venv\Lib\site-packages\PyQt5\Qt5\plugins"

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
	--onedir `
	--windowed `
	--log-level "INFO" `
	--name $APP_NAME `
	--add-data "config;config\" `
	--paths "." `
	$MAIN_SCRIPT

# Removing build directory and writing message
Remove-Item -Recurse -Force $BUILD_DIR -ErrorAction SilentlyContinue
Write-Host "Build completed. Executable is in $DIST_DIR\$APP_NAME"

# Create drivers directory in the output folder
$DRIVERS_DIR = "$DIST_DIR\$APP_NAME\drivers"
Write-Host "Creating drivers directory..."
New-Item -Path $DRIVERS_DIR -ItemType Directory -Force

# Extract zip file contents into drivers directory
$ZIP_FILE = ".\adapter-espada-usbrs-485_drajver.zip"
Write-Host "Extracting driver files from $ZIP_FILE..."

# Check PowerShell version
$PSVersion = $PSVersionTable.PSVersion.Major

if ($PSVersion -ge 5) {
	# Use Expand-Archive for PowerShell 5+
	Expand-Archive -Path $ZIP_FILE -DestinationPath $DRIVERS_DIR -Force
}
else {
	# Fallback for PowerShell < 5 (e.g., Windows 7)
	try {
		# Attempt to load the assembly
		Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop
		[System.IO.Compression.ZipFile]::ExtractToDirectory($ZIP_FILE, $DRIVERS_DIR)
	}
 catch {
		Write-Host "System.IO.Compression.FileSystem assembly not found. Using alternative method..."
		# Use COM object for ZIP extraction (Windows built-in)
		$shell = New-Object -ComObject Shell.Application
		$zip = $shell.NameSpace((Resolve-Path $ZIP_FILE).Path)
		foreach ($item in $zip.Items()) {
			$shell.Namespace((Resolve-Path $DRIVERS_DIR).Path).CopyHere($item)
		}
	}
}

Write-Host "Driver files copied to $DRIVERS_DIR"

# Remove ports.yaml file from the distribution
$PORTS_CONFIG_FILE = "$DIST_DIR\$APP_NAME\_internal\config\ports.yaml"
if (Test-Path $PORTS_CONFIG_FILE) {
	Write-Host "Removing ports configuration file from distribution..."
	Remove-Item -Force $PORTS_CONFIG_FILE -ErrorAction SilentlyContinue
	Write-Host "Ports configuration file removed from distribution."
}
else {
	Write-Host "Ports configuration [$PORTS_CONFIG_FILE] file not found in distribution."
}

# Create a ZIP archive of the application directory
Write-Host "Creating ZIP archive of the application..."
$ZIP_OUTPUT = "$DIST_DIR\$APP_NAME.zip"
if (Test-Path $ZIP_OUTPUT) {
	Remove-Item -Force $ZIP_OUTPUT -ErrorAction SilentlyContinue
}

# Using Compress-Archive (or fallback for PowerShell < 5)
if ($PSVersion -ge 5) {
	Compress-Archive -Path "$DIST_DIR\$APP_NAME\*" -DestinationPath $ZIP_OUTPUT -CompressionLevel Optimal
}
else {
	try {
		Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop
		$compressionLevel = [System.IO.Compression.CompressionLevel]::Optimal
		[System.IO.Compression.ZipFile]::CreateFromDirectory("$DIST_DIR\$APP_NAME", $ZIP_OUTPUT, $compressionLevel, $false)
	}
 catch {
		Write-Host "System.IO.Compression.FileSystem assembly not found. Skipping ZIP creation."
	}
}

Write-Host "ZIP archive created: $ZIP_OUTPUT"
