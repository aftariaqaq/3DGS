param(
    [Parameter(Mandatory = $true)][string]$CapturePath,
    [Parameter(Mandatory = $true)][string]$JobId,
    [int]$MaxFrames = 700,
    [string]$JobsRoot = "data\jobs",
    [switch]$SkipPrepare
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$env:PYTHONPATH = $repoRoot

$command = if ($SkipPrepare) { "import-capture" } else { "process-capture" }

python -m packages.pipeline $command `
    $CapturePath `
    --jobs-root (Join-Path $repoRoot $JobsRoot) `
    --job-id $JobId `
    --max-frames $MaxFrames
