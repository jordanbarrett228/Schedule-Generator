param(
  [string]$OutDir = "portable_build"
)

Write-Host "Creating portable build in: $OutDir"
if (Test-Path $OutDir) { Remove-Item $OutDir -Recurse -Force }
New-Item -ItemType Directory -Path $OutDir | Out-Null

# Copy exe
$exe = "backend\dist\run_app.exe"
if (Test-Path $exe) {
  Copy-Item $exe -Destination $OutDir
  Write-Host "Copied exe: $exe"
} else {
  Write-Warning "Exe not found at $exe. Make sure you built the backend exe first."
}

# Copy backend static (frontend build) if present
$staticSrc = "backend\app\static\dist"
if (Test-Path $staticSrc) {
  Copy-Item $staticSrc -Destination (Join-Path $OutDir "static") -Recurse
  Write-Host "Copied frontend static from $staticSrc"
} else {
  Write-Warning "Static frontend not found at $staticSrc. Consider running a frontend build and copying dist into backend/app/static/dist"
}

# Copy DB if present
$db = "backend\data\schedule.db"
if (Test-Path $db) {
  Copy-Item $db -Destination $OutDir
  Write-Host "Copied DB: $db"
} else {
  Write-Warning "Database not found at $db. The app will create a fresh DB on first run if needed."
}

# Create a small run script
$runPs = @"
cd "$(Split-Path -Path $MyInvocation.MyCommand.Definition -Parent)"
.
\run_app.exe
"@
$runPsPath = Join-Path $OutDir "run.ps1"
Set-Content -Path $runPsPath -Value $runPs -Encoding UTF8

$runBat = "@echo off`ncd /d %~dp0`nstart run_app.exe"
Set-Content -Path (Join-Path $OutDir "run.bat") -Value $runBat -Encoding ASCII

Write-Host "Portable build assembled. Copy the '$OutDir' folder to a flash drive and run run.bat (Windows)."
