param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$apiRoot = Join-Path $repoRoot "apps\api"

$env:PYTHONPATH = $apiRoot
python -m uvicorn app.main:app --host $HostName --port $Port
