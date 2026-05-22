param(
    [Parameter(Mandatory = $true)][string]$InputVideo,
    [string]$JobId = "job_test_001",
    [int]$Fps = 1,
    [int]$MaxFrames = 80,
    [int]$Iterations = 500,
    [int]$OpenSplatDownscaleFactor = 1,
    [int]$OpenSplatNumDownscales = 2
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$localToolsRoot = "D:\.codex_tools"

function Find-Executable {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [string[]]$FallbackPaths = @()
    )

    $fromPath = Get-Command $Command -ErrorAction SilentlyContinue
    if ($fromPath) {
        return $fromPath.Source
    }

    foreach ($path in $FallbackPaths) {
        if (Test-Path $path) {
            return (Resolve-Path $path).Path
        }
    }

    throw "Required command not found: $Command"
}

function Invoke-LoggedCommand {
    param(
        [Parameter(Mandatory = $true)][string[]]$Command,
        [Parameter(Mandatory = $true)][string]$LogPath,
        [string]$WorkingDirectory = $repoRoot
    )

    $logDirectory = Split-Path -Parent $LogPath
    New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null

    "COMMAND: $($Command -join ' ')" | Set-Content -Path $LogPath

    $stdoutPath = [System.IO.Path]::GetTempFileName()
    $stderrPath = [System.IO.Path]::GetTempFileName()

    $process = Start-Process `
        -FilePath $Command[0] `
        -ArgumentList $Command[1..($Command.Count - 1)] `
        -WorkingDirectory $WorkingDirectory `
        -NoNewWindow `
        -Wait `
        -PassThru `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath

    if (Test-Path $stdoutPath) {
        Get-Content $stdoutPath | Add-Content -Path $LogPath
        Remove-Item $stdoutPath -Force
    }

    if (Test-Path $stderrPath) {
        Get-Content $stderrPath | Add-Content -Path $LogPath
        Remove-Item $stderrPath -Force
    }

    if ($process.ExitCode -ne 0) {
        throw "Command failed with exit code $($process.ExitCode): $($Command -join ' ')"
    }
}

function Limit-Frames {
    param(
        [Parameter(Mandatory = $true)][string]$ImagesDir,
        [Parameter(Mandatory = $true)][int]$MaxFrames
    )

    $frames = @(Get-ChildItem -Path $ImagesDir -Filter "*.jpg" | Sort-Object Name)
    if ($frames.Count -le $MaxFrames) {
        return $frames.Count
    }

    for ($i = $MaxFrames; $i -lt $frames.Count; $i++) {
        Remove-Item -LiteralPath $frames[$i].FullName -Force
    }

    return $MaxFrames
}

if (!(Test-Path $InputVideo)) {
    throw "Input video not found: $InputVideo"
}

if ($Fps -lt 1) {
    throw "Fps must be >= 1"
}

if ($MaxFrames -lt 1) {
    throw "MaxFrames must be >= 1"
}

if ($Iterations -lt 1) {
    throw "Iterations must be >= 1"
}

if ($OpenSplatDownscaleFactor -lt 1) {
    throw "OpenSplatDownscaleFactor must be >= 1"
}

if ($OpenSplatNumDownscales -lt 0) {
    throw "OpenSplatNumDownscales must be >= 0"
}

$ffmpeg = Find-Executable `
    -Command "ffmpeg" `
    -FallbackPaths @(
        "C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe"
    )

$colmap = Find-Executable `
    -Command "colmap" `
    -FallbackPaths @(
        "$localToolsRoot\colmap-x64-windows-nocuda\bin\colmap.exe"
    )

$docker = Find-Executable -Command "docker"

$jobRoot = Join-Path $repoRoot "data\jobs\$JobId"
$inputDir = Join-Path $jobRoot "input"
$imagesDir = Join-Path $jobRoot "images"
$colmapDir = Join-Path $jobRoot "colmap"
$sparseDir = Join-Path $colmapDir "sparse"
$opensplatDir = Join-Path $jobRoot "opensplat"
$logsDir = Join-Path $jobRoot "logs"

New-Item -ItemType Directory -Force -Path $inputDir, $imagesDir, $colmapDir, $sparseDir, $opensplatDir, $logsDir | Out-Null

$copiedVideo = Join-Path $inputDir "input.mp4"
Copy-Item -LiteralPath $InputVideo -Destination $copiedVideo -Force

Invoke-LoggedCommand `
    -Command @($ffmpeg, "-y", "-i", $copiedVideo, "-vf", "fps=$Fps", (Join-Path $imagesDir "frame_%06d.jpg")) `
    -LogPath (Join-Path $logsDir "extract_frames.log")

$frameCount = Limit-Frames -ImagesDir $imagesDir -MaxFrames $MaxFrames
if ($frameCount -lt 2) {
    throw "Need at least 2 frames for COLMAP, got $frameCount"
}

Invoke-LoggedCommand `
    -Command @(
        $colmap,
        "feature_extractor",
        "--database_path", (Join-Path $colmapDir "database.db"),
        "--image_path", $imagesDir,
        "--FeatureExtraction.use_gpu", "0",
        "--FeatureExtraction.max_image_size", "1600"
    ) `
    -LogPath (Join-Path $logsDir "colmap_features.log")

Invoke-LoggedCommand `
    -Command @(
        $colmap,
        "sequential_matcher",
        "--database_path", (Join-Path $colmapDir "database.db"),
        "--FeatureMatching.use_gpu", "0",
        "--SiftMatching.cpu_brute_force_matcher", "1"
    ) `
    -LogPath (Join-Path $logsDir "colmap_matching.log")

Invoke-LoggedCommand `
    -Command @(
        $colmap,
        "mapper",
        "--database_path", (Join-Path $colmapDir "database.db"),
        "--image_path", $imagesDir,
        "--output_path", $sparseDir
    ) `
    -LogPath (Join-Path $logsDir "colmap_mapping.log")

$jobRootDocker = ($jobRoot -replace "\\", "/")

Invoke-LoggedCommand `
    -Command @(
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
    ) `
    -LogPath (Join-Path $logsDir "opensplat.log")

$result = Join-Path $opensplatDir "splat.ply"
if (!(Test-Path $result)) {
    throw "OpenSplat output not found: $result"
}

Write-Host "Pipeline complete"
Write-Host "Frames: $frameCount"
Write-Host "Output: $result"
