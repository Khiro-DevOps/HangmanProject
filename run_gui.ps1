<#
PowerShell helper to run gui.py when 'python' isn't on PATH.
Tries `py`, `python`, `python3`, then common install locations.
If none found, prints instructions to install Python.
#>

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$guiPath = Join-Path $scriptDir 'gui.py'

function Invoke-PythonRun($cmd) {
    $exe = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($exe) {
        Write-Host "Launching with $cmd..."
        & $cmd $guiPath
        exit $LASTEXITCODE
    }
}

foreach ($c in @('py', 'python', 'python3')) {
    Invoke-PythonRun $c
}

# Try common installation paths
$possible = @(
    "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe",
    "$env:ProgramFiles\Python39\python.exe",
    "$env:ProgramFiles\Python310\python.exe",
    "C:\Python39\python.exe",
    "C:\Python310\python.exe"
)

foreach ($p in $possible) {
    if (Test-Path $p) {
        Write-Host "Found Python at $p; launching..."
        & $p $guiPath
        exit $LASTEXITCODE
    }
}

Write-Host "Python not found. Install Python from https://www.python.org/downloads/ and enable 'Add Python to PATH' in the installer." -ForegroundColor Yellow
Write-Host "After installing, reopen PowerShell and run:" -ForegroundColor Yellow
Write-Host "    py gui.py" -ForegroundColor Yellow
exit 1