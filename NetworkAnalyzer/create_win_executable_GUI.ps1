# Check for Python 3.12
$pythonVersion = "3.12"
$pythonPath = $null

# Function to check Python version
function Get-PythonVersion {
    param (
        [string]$pythonExecutable
    )
    $versionInfo = & $pythonExecutable --version 2>&1
    if ($versionInfo -match "Python (\d+)\.(\d+)\.(\d+)") {
        return "$($matches[1]).$($matches[2])"
    }
    return $null
}

# Search for installed Python 3.12
$pythonPath = Get-Command python -ErrorAction SilentlyContinue
if ($pythonPath) {
    $installedVersion = Get-PythonVersion $pythonPath
    if ($installedVersion -ne $pythonVersion) {
        $pythonPath = $null
    }
}

# Install Python 3.12 if not found
if (-not $pythonPath) {
    Write-Host "Python $pythonVersion not found. Installing..."
    $pythonInstallerUrl = "https://www.python.org/ftp/python/$pythonVersion.0/python-$pythonVersion.0-amd64.exe"
    $installerPath = "$env:TEMP\python-installer.exe"
    Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $installerPath
    Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
    Remove-Item -Path $installerPath

    $pythonPath = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonPath) {
        Write-Error "Python $pythonVersion installation failed."
        exit 1
    }
}

# Install dependencies
Write-Host "Installing dependencies from requirements.txt..."
& $pythonPath -m pip install --upgrade pip
& $pythonPath -m pip install -r requirements.txt

# Define relative paths
$scriptPath = (Get-Location).Path
$langsPath = Join-Path $scriptPath "langs"
$imgsPath = Join-Path $scriptPath "imgs"
$utilPath = Join-Path $scriptPath "util"
$networkAnalyzerPath = Join-Path $scriptPath "network_analyzer"
$initPath = Join-Path $scriptPath "__init__.py"
$mainScriptPath = Join-Path $scriptPath "na-gui.py"

# Run PyInstaller
Write-Host "Running PyInstaller..."
& $pythonPath -m PyInstaller --noconfirm --onedir --name "na-gui" --log-level "INFO" `
    --add-data "$langsPath;langs/" `
    --add-data "$utilPath;util/" `
    --add-data "$networkAnalyzerPath;network_analyzer/" `
    --add-data "$initPath;." `
    --hidden-import "schedule" `
    --hidden-import "psutil" `
    --hidden-import "pandas" `
    --hidden-import "matplotlib" `
    --hidden-import "numpy" `
    --hidden-import "speedtest" `
    --hidden-import "PyQt5" `
    --hidden-import "json" `
    $mainScriptPath

Write-Host "Moving langs directory to the correct location..."
$distDir = Join-Path $scriptPath "dist\na-gui"
Move-Item -Path "$distDir\_internal\langs" -Destination "$distDir\langs"
Copy-Item -Path $imgsPath -Destination "$distDir\imgs"
