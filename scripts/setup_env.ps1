Param(
    [string]$EnvName = "tb"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' was not found. Install Python 3.11+ first."
}

if (-not (Test-Path $EnvName)) {
    py -m venv $EnvName
}

$pythonExe = Join-Path $EnvName "Scripts\python.exe"
& $pythonExe -m pip install --upgrade pip

if (Test-Path "requirements.txt") {
    & $pythonExe -m pip install -r requirements.txt
} else {
    & $pythonExe -m pip install fastapi uvicorn
    & $pythonExe -m pip freeze | Out-File -Encoding ascii requirements.txt
}

Write-Output "Environment '$EnvName' is ready."
Write-Output "Activate with: .\\$EnvName\\Scripts\\Activate.ps1"
