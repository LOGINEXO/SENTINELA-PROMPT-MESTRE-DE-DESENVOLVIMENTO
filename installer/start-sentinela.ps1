$ErrorActionPreference = "Stop"
$ProjectDir = Join-Path $env:LOCALAPPDATA "Sentinela"
$Starter = Join-Path $ProjectDir "scripts\start-windows.ps1"

if (-not (Test-Path $Starter)) {
    Write-Host "O Sentinela ainda nao esta instalado. Abra 'Instalar / reparar dependencias' no menu Iniciar." -ForegroundColor Yellow
    exit 1
}

Start-Process "http://127.0.0.1:8080"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Starter
