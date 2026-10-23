$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$ProjectDir = Join-Path $env:LOCALAPPDATA "Sentinela"
$ZipPath = Join-Path $env:TEMP "sentinela-source.zip"
$ExtractDir = Join-Path $env:TEMP ("sentinela-source-" + [guid]::NewGuid().ToString("N"))
$RepoUrl = "https://github.com/LOGINEXO/SENTINELA-PROMPT-MESTRE-DE-DESENVOLVIMENTO/archive/refs/heads/main.zip"

function Has-Command([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}
function Refresh-Path {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user;$env:Path"
}
function Install-Package([string]$Id) {
    Write-Host "Instalando $Id com o Gerenciador de Pacotes do Windows..." -ForegroundColor Cyan
    & winget install --id $Id --exact --source winget --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "winget retornou codigo $LASTEXITCODE ao instalar $Id. Vou verificar se o programa ficou disponivel."
    }
}

Write-Host "SENTINELA — INSTALADOR" -ForegroundColor Green
Write-Host "Este instalador baixa o codigo-fonte do repositorio oficial e prepara as dependencias."
Write-Host "A interface permanece local em http://127.0.0.1:8080."
if (-not (Has-Command "winget")) {
    throw "O winget nao foi encontrado. Instale/atualize 'App Installer' pela Microsoft Store e execute novamente."
}

if (-not (Has-Command "py") -and -not (Has-Command "python")) {
    Install-Package "Python.Python.3.12"
}
if (-not (Has-Command "php")) {
    # PHP NTS is the CLI-oriented package published in the WinGet catalog.
    Install-Package "PHP.PHP.NTS.8.4"
}
Refresh-Path

$PythonExe = $null
if (Has-Command "py") {
    $candidate = & py -3.12 -c "import sys; print(sys.executable)" 2>$null
    if ($LASTEXITCODE -eq 0 -and $candidate) { $PythonExe = ($candidate | Select-Object -First 1).Trim() }
}
if (-not $PythonExe -and (Has-Command "python")) {
    $candidate = & python -c "import sys; print(sys.executable)" 2>$null
    if ($LASTEXITCODE -eq 0 -and $candidate) { $PythonExe = ($candidate | Select-Object -First 1).Trim() }
}
if (-not $PythonExe) {
    throw "Python nao foi encontrado apos a instalacao. Reinicie o Windows e use o atalho 'Instalar / reparar dependencias'."
}
& $PythonExe -c "import sys; raise SystemExit(0 if sys.version_info -ge (3,11) else 1)"
if ($LASTEXITCODE -ne 0) { throw "O Sentinela exige Python 3.11 ou superior." }

if (-not (Has-Command "php")) {
    throw "PHP CLI nao foi encontrado no PATH. Reinicie o Windows e execute 'Instalar / reparar dependencias' novamente."
}
php -r "exit(version_compare(PHP_VERSION, '8.0.0', '>=') ? 0 : 1);"
if ($LASTEXITCODE -ne 0) { throw "O Sentinela exige PHP CLI 8.0 ou superior." }

if (Test-Path $ProjectDir) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backup = "$ProjectDir-backup-$stamp"
    Move-Item -Path $ProjectDir -Destination $backup
    Write-Host "Instalacao anterior preservada em $backup"
}
New-Item -ItemType Directory -Path $ProjectDir -Force | Out-Null

Write-Host "Baixando o codigo-fonte do GitHub..."
Invoke-WebRequest -Uri $RepoUrl -OutFile $ZipPath
New-Item -ItemType Directory -Path $ExtractDir -Force | Out-Null
Expand-Archive -Path $ZipPath -DestinationPath $ExtractDir -Force
$RepoRoot = Get-ChildItem $ExtractDir -Directory | Select-Object -First 1
if (-not $RepoRoot) { throw "O arquivo baixado nao contem a pasta do projeto." }
Copy-Item -Path (Join-Path $RepoRoot.FullName "*") -Destination $ProjectDir -Recurse -Force

$Installer = Join-Path $ProjectDir "scripts\install-windows.ps1"
if (-not (Test-Path $Installer)) {
    throw "O repositorio baixado nao contem scripts\install-windows.ps1. Confira a branch main."
}
Write-Host "Preparando o ambiente Python do projeto..."
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Installer
if ($LASTEXITCODE -ne 0) { throw "A instalacao das dependencias do Sentinela falhou." }

Write-Host ""
Write-Host "Instalacao concluida!" -ForegroundColor Green
Write-Host "Abra o atalho Sentinela no menu Iniciar."
Write-Host "Pasta do projeto: $ProjectDir"
Write-Host "Painel local: http://127.0.0.1:8080"
