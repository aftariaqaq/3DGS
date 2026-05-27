param(
    [Parameter(Mandatory = $true)][string]$JobId,
    [int]$Iterations = 25000,
    [switch]$UseDocker,
    [string]$ImageName = "3dgs-runtime:rtx5090",
    [string]$GpuDevices = "4,5,6,7"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$jobRoot = Join-Path $repoRoot "data\jobs\$JobId"
$imagesDir = Join-Path $jobRoot "images"
$colmapSparseDir = Join-Path $jobRoot "colmap\sparse"
$nerfstudioDir = Join-Path $jobRoot "nerfstudio"
$nerfstudioData = Join-Path $nerfstudioDir "data"
$nerfstudioImages = Join-Path $nerfstudioData "images"
$nerfstudioSparse = Join-Path $nerfstudioData "colmap\sparse"
$nerfstudioSparseZero = Join-Path $nerfstudioSparse "0"
$nerfstudioOutputs = Join-Path $nerfstudioDir "outputs"
$exportDir = Join-Path $nerfstudioDir "exports"
$logsDir = Join-Path $jobRoot "logs"
$processLog = Join-Path $logsDir "nerfstudio-process-data.log"
$trainLog = Join-Path $logsDir "splatfacto.log"
$exportLog = Join-Path $logsDir "splatfacto-export.log"

if (!(Test-Path $imagesDir)) {
    throw "Images directory not found: $imagesDir"
}
if (!(Test-Path (Join-Path $colmapSparseDir "0"))) {
    throw "COLMAP sparse/0 directory not found: $(Join-Path $colmapSparseDir '0')"
}

New-Item -ItemType Directory -Force -Path $nerfstudioData, $nerfstudioOutputs, $exportDir, $logsDir | Out-Null
Remove-Item -LiteralPath $nerfstudioImages -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $nerfstudioSparse -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $nerfstudioSparse | Out-Null
Copy-Item -LiteralPath $imagesDir -Destination $nerfstudioImages -Recurse -Force
Copy-Item -LiteralPath (Join-Path $colmapSparseDir "0") -Destination $nerfstudioSparseZero -Recurse -Force

function Invoke-Logged {
    param(
        [Parameter(Mandatory = $true)][string[]]$Command,
        [Parameter(Mandatory = $true)][string]$LogPath
    )

    "COMMAND: $($Command -join ' ')" | Set-Content -Path $LogPath
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        & $Command[0] @($Command[1..($Command.Count - 1)]) 2>&1 | ForEach-Object {
            Add-Content -Path $LogPath -Value $_.ToString()
        }
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($exitCode -ne 0) {
        throw "Command failed with exit code ${exitCode}. See $LogPath"
    }
}

if ($UseDocker) {
    $docker = (Get-Command "docker" -ErrorAction Stop).Source
    $repoRootDocker = ($repoRoot.Path -replace "\\", "/")
    $processCommand = @(
        $docker, "run", "--rm", "--gpus", "device=$GpuDevices",
        "-e", "CUDA_VISIBLE_DEVICES=0,1,2,3",
        "-v", "${repoRootDocker}:/workspace",
        "-w", "/workspace",
        $ImageName,
        "ns-process-data", "images",
        "--data", "data/jobs/$JobId/nerfstudio/data/images",
        "--output-dir", "data/jobs/$JobId/nerfstudio/data",
        "--skip-colmap",
        "--skip-image-processing",
        "--colmap-model-path", "data/jobs/$JobId/nerfstudio/data/colmap/sparse/0"
    )
    $trainCommand = @(
        $docker, "run", "--rm", "--gpus", "device=$GpuDevices",
        "-e", "CUDA_VISIBLE_DEVICES=0,1,2,3",
        "-v", "${repoRootDocker}:/workspace",
        "-w", "/workspace",
        $ImageName,
        "ns-train", "splatfacto",
        "--data", "data/jobs/$JobId/nerfstudio/data",
        "--output-dir", "data/jobs/$JobId/nerfstudio/outputs",
        "--experiment-name", $JobId,
        "--max-num-iterations", "$Iterations",
        "--vis", "viewer"
    )
} else {
    $nsProcessData = (Get-Command "ns-process-data" -ErrorAction Stop).Source
    $nsTrain = (Get-Command "ns-train" -ErrorAction Stop).Source
    $processCommand = @(
        $nsProcessData, "images",
        "--data", $nerfstudioImages,
        "--output-dir", $nerfstudioData,
        "--skip-colmap",
        "--skip-image-processing",
        "--colmap-model-path", $nerfstudioSparseZero
    )
    $trainCommand = @(
        $nsTrain, "splatfacto",
        "--data", $nerfstudioData,
        "--output-dir", $nerfstudioOutputs,
        "--experiment-name", $JobId,
        "--max-num-iterations", "$Iterations",
        "--vis", "viewer"
    )
}

Invoke-Logged -Command $processCommand -LogPath $processLog
Invoke-Logged -Command $trainCommand -LogPath $trainLog

$config = Get-ChildItem -LiteralPath $nerfstudioOutputs -Recurse -Filter "config.yml" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (!$config) {
    throw "Splatfacto config.yml not found under $nerfstudioOutputs"
}

if ($UseDocker) {
    $docker = (Get-Command "docker" -ErrorAction Stop).Source
    $repoRootDocker = ($repoRoot.Path -replace "\\", "/")
    $configPath = ($config.FullName.Substring($repoRoot.Path.Length + 1) -replace "\\", "/")
    $exportCommand = @(
        $docker, "run", "--rm", "--gpus", "device=$GpuDevices",
        "-e", "CUDA_VISIBLE_DEVICES=0,1,2,3",
        "-v", "${repoRootDocker}:/workspace",
        "-w", "/workspace",
        $ImageName,
        "ns-export", "gaussian-splat",
        "--load-config", $configPath,
        "--output-dir", "data/jobs/$JobId/nerfstudio/exports"
    )
} else {
    $nsExport = (Get-Command "ns-export" -ErrorAction Stop).Source
    $exportCommand = @(
        $nsExport, "gaussian-splat",
        "--load-config", $config.FullName,
        "--output-dir", $exportDir
    )
}

Invoke-Logged -Command $exportCommand -LogPath $exportLog

$result = Get-ChildItem -LiteralPath $exportDir -Filter "*.ply" | Select-Object -First 1
if (!$result) {
    throw "Splatfacto export not found under $exportDir"
}

Write-Host "Splatfacto complete"
Write-Host "Output: $($result.FullName)"
