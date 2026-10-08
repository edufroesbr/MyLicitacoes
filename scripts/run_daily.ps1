# Wrapper para o Windows Task Scheduler: garante Postgres de pe, schema
# atualizado, roda a captura diaria e loga tudo (a task roda sem console).
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

Get-Content ".env" | ForEach-Object {
    if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
        [System.Environment]::SetEnvironmentVariable($Matches[1], $Matches[2])
    }
}

docker compose up -d postgres
Start-Sleep -Seconds 5  # ponytail: espera fixa; trocar por retry de conexao se um dia isto nao bastar

uv run alembic upgrade head

$logDir = "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir "run_daily.log"

Add-Content -Path $logFile -Value "=== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ===" -Encoding utf8
uv run python -m app.scheduler.run_daily | Out-File -FilePath $logFile -Append -Encoding utf8
