Param(
    [string]$EnvName = "tb"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' was not found. Install Python 3.11+ first."
}

$basePython = (py -c "import sys; print(sys.executable)")
if (-not (Test-Path $basePython)) {
    throw "Python launcher resolved to '$basePython', which does not exist. Check your Python installation."
}
Write-Output "Using Python: $basePython"

$pythonExe = Join-Path $EnvName "Scripts\python.exe"

if (Test-Path $EnvName) {
    $cfg = Join-Path $EnvName "pyvenv.cfg"
    $homeDir = (Get-Content $cfg | Select-String '^home\s*=\s*(.+)$').Matches[0].Groups[1].Value.Trim()
    if (-not (Test-Path (Join-Path $homeDir "python.exe"))) {
        Write-Output "Existing venv '$EnvName' is broken (base Python missing), recreating..."
        Remove-Item -Recurse -Force $EnvName
    }
}

if (-not (Test-Path $EnvName)) {
    & $basePython -m venv $EnvName
}
& $pythonExe -m pip install --upgrade pip

if (Test-Path "requirements.txt") {
    & $pythonExe -m pip install -r requirements.txt
} else {
    & $pythonExe -m pip install fastapi uvicorn
    & $pythonExe -m pip freeze | Out-File -Encoding ascii requirements.txt
}

Write-Output "Environment '$EnvName' is ready."
Write-Output "Activate with: .\\$EnvName\\Scripts\\Activate.ps1"
