param(
    [Parameter(Mandatory = $true)][string]$CapturePath,
    [Parameter(Mandatory = $true)][string]$JobId,
    [int]$MaxFrames = 700,
    [string]$JobsRoot = "data\jobs"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$env:PYTHONPATH = $repoRoot

python -m packages.pipeline import-capture `
    $CapturePath `
    --jobs-root (Join-Path $repoRoot $JobsRoot) `
    --job-id $JobId `
    --max-frames $MaxFrames
