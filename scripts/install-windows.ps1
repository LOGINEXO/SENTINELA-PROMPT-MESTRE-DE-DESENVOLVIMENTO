$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

function Stop-WithError([string]$Message) {
    Write-Error $Message
    exit 1
}

$PythonExe = $null
$PyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($PyLauncher) {
    try {
        $Candidate = (& py -3.11 -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1)
        if ($LASTEXITCODE -eq 0 -and $Candidate) { $PythonExe = $Candidate.Trim() }
    } catch { }
}
if (-not $PythonExe) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        try {
            $Candidate = (& python -c "import sys; print(sys.executable)" 2>$null | Select-Object -First 1)
            if ($LASTEXITCODE -eq 0 -and $Candidate) { $PythonExe = $Candidate.Trim() }
        } catch { }
    }
}
if (-not $PythonExe) { Stop-WithError "Python 3.11+ não encontrado. Instale Python 3.11 ou superior e tente novamente." }

& $PythonExe -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) { Stop-WithError "É necessário Python 3.11 ou superior." }

$PhpCommand = Get-Command php -ErrorAction SilentlyContinue
if (-not $PhpCommand) { Stop-WithError "PHP CLI 8.0+ não encontrado. Instale PHP 8.0 ou superior e adicione php.exe ao PATH." }
php -r "exit(version_compare(PHP_VERSION, '8.0.0', '>=') ? 0 : 1);"
if ($LASTEXITCODE -ne 0) { Stop-WithError "É necessário PHP 8.0 ou superior." }

& $PythonExe -m venv .venv
if ($LASTEXITCODE -ne 0) { Stop-WithError "Falha ao criar o ambiente virtual Python." }
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { Stop-WithError "Falha ao atualizar pip." }
& $VenvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Stop-WithError "Falha ao instalar dependências." }

$PassiveScope = Join-Path $Root "config\authorized_targets.txt"
$ActiveScope = Join-Path $Root "config\authorized_active_targets.txt"
if (-not (Test-Path $PassiveScope)) { Copy-Item (Join-Path $Root "config\authorized_targets.example.txt") $PassiveScope }
if (-not (Test-Path $ActiveScope)) { Copy-Item (Join-Path $Root "config\authorized_active_targets.example.txt") $ActiveScope }
New-Item -ItemType Directory -Force -Path (Join-Path $Root "reports") | Out-Null

Write-Host ""
Write-Host "Instalação concluída."
Write-Host "Para iniciar, execute: .\scripts\start-windows.ps1"
Write-Host "Depois abra http://127.0.0.1:8080 no navegador."
