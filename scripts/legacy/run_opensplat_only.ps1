param(
    [Parameter(Mandatory = $true)][string]$JobId,
    [int]$Iterations = 2500,
    [int]$OpenSplatDownscaleFactor = 4,
    [int]$OpenSplatNumDownscales = 2
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$docker = (Get-Command "docker" -ErrorAction Stop).Source
$jobRoot = Join-Path $repoRoot "data\jobs\$JobId"
$colmapDir = Join-Path $jobRoot "colmap"
$imagesDir = Join-Path $jobRoot "images"
$opensplatDir = Join-Path $jobRoot "opensplat"
$logsDir = Join-Path $jobRoot "logs"
$logPath = Join-Path $logsDir "opensplat.log"

if (!(Test-Path $colmapDir)) {
    throw "COLMAP directory not found: $colmapDir"
}
if (!(Test-Path $imagesDir)) {
    throw "Images directory not found: $imagesDir"
}

New-Item -ItemType Directory -Force -Path $opensplatDir, $logsDir | Out-Null
Remove-Item -LiteralPath (Join-Path $opensplatDir "splat.ply") -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $opensplatDir "cameras.json") -Force -ErrorAction SilentlyContinue

$jobRootDocker = ($jobRoot -replace "\\", "/")
$command = @(
    $docker,
    "run", "--rm",
    "-v", "${jobRootDocker}:/work",
    "opensplat-cpu:local",
    "--cpu",
    "-n", "$Iterations",
    "--downscale-factor", "$OpenSplatDownscaleFactor",
    "--num-downscales", "$OpenSplatNumDownscales",
    "-o", "/work/opensplat/splat.ply",
    "--colmap-image-path", "/work/images",
    "/work/colmap"
)

"COMMAND: $($command -join ' ')" | Set-Content -Path $logPath
$ErrorActionPreference = "Continue"
& $docker @($command[1..($command.Count - 1)]) 2>&1 | ForEach-Object {
    Add-Content -Path $logPath -Value $_.ToString()
}
$exitCode = $LASTEXITCODE
$ErrorActionPreference = "Stop"

if ($exitCode -ne 0) {
    throw "OpenSplat failed with exit code ${exitCode}"
}

$result = Join-Path $opensplatDir "splat.ply"
if (!(Test-Path $result)) {
    throw "OpenSplat output not found: $result"
}

Write-Host "OpenSplat complete"
Write-Host "Output: $result"
