$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Ambiente não instalado. Execute .\scripts\install-windows.ps1 primeiro."
}
$PhpCommand = Get-Command php -ErrorAction SilentlyContinue
if (-not $PhpCommand) { throw "PHP CLI 8.0+ não encontrado ou não está no PATH." }
php -r "exit(version_compare(PHP_VERSION, '8.0.0', '>=') ? 0 : 1);"
if ($LASTEXITCODE -ne 0) { throw "É necessário PHP 8.0 ou superior." }

New-Item -ItemType Directory -Force -Path (Join-Path $Root "reports") | Out-Null
$env:SENTINELA_PYTHON = $Python
$WorkerOut = Join-Path $Root "reports\worker.stdout.log"
$WorkerErr = Join-Path $Root "reports\worker.stderr.log"
$Worker = Start-Process -FilePath $Python -ArgumentList @("-m", "sentinela.queue_worker") -WorkingDirectory $Root -PassThru -WindowStyle Hidden -RedirectStandardOutput $WorkerOut -RedirectStandardError $WorkerErr
try {
    Write-Host "Sentinela ativo em http://127.0.0.1:8080"
    Write-Host "Mantenha esta janela aberta. Pressione Ctrl+C para encerrar."
    php -S 127.0.0.1:8080 -t web
}
finally {
    if ($Worker -and -not $Worker.HasExited) {
        Stop-Process -Id $Worker.Id -Force -ErrorAction SilentlyContinue
    }
}
