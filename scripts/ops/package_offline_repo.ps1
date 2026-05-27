param(
    [string]$OutputDir = "artifacts",
    [string]$PackageName = "",
    [switch]$IncludeTest1Video
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$outputRoot = Join-Path $repoRoot $OutputDir
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

if ([string]::IsNullOrWhiteSpace($PackageName)) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $PackageName = "3dgs-repo-splatfacto-$timestamp.tar"
}

$archivePath = Join-Path $outputRoot $PackageName
if (Test-Path $archivePath) {
    Remove-Item -LiteralPath $archivePath -Force
}

$excludeArgs = @(
    "--exclude=.git",
    "--exclude=.pytest_cache",
    "--exclude=artifacts",
    "--exclude=data",
    "--exclude=docs/superpowers",
    "--exclude=docs/phase-1-verification.md",
    "--exclude=scripts/legacy",
    "--exclude=docker/legacy",
    "--exclude=.worktrees",
    "--exclude=worktrees",
    "--exclude=apps/api/.venv",
    "--exclude=apps/capture-android/.gradle",
    "--exclude=apps/capture-android/**/build",
    "--exclude=**/__pycache__",
    "--exclude=**/*.pyc",
    "--exclude=**/*.pyo",
    "--exclude=**/node_modules",
    "--exclude=**/dist"
)

if ($IncludeTest1Video) {
    $excludeArgs += @(
        "--exclude=test_video/test0.mp4",
        "--exclude=test_video/test2.mp4"
    )
} else {
    $excludeArgs += "--exclude=test_video"
}

& tar -cf $archivePath @excludeArgs -C $repoRoot .
if ($LASTEXITCODE -ne 0) {
    throw "tar failed with exit code $LASTEXITCODE"
}

Write-Host "Offline repo archive created:"
Write-Host $archivePath
