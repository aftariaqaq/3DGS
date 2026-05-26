param(
    [string]$OutputDir = "artifacts",
    [string]$PackageName = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$outputRoot = Join-Path $repoRoot $OutputDir
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null

if ([string]::IsNullOrWhiteSpace($PackageName)) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $PackageName = "3dgs-cuda-package-$timestamp.zip"
}

$archivePath = Join-Path $outputRoot $PackageName
$stagingRoot = Join-Path $outputRoot "cuda-package-staging"

$resolvedOutputRoot = (Resolve-Path $outputRoot).Path
if (Test-Path $stagingRoot) {
    $resolvedStagingRoot = (Resolve-Path $stagingRoot).Path
    if (!$resolvedStagingRoot.StartsWith($resolvedOutputRoot)) {
        throw "Refusing to remove staging path outside output directory: $resolvedStagingRoot"
    }
    Remove-Item -LiteralPath $resolvedStagingRoot -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $stagingRoot | Out-Null

$includeDirs = @("apps", "packages", "docker", "docs", "scripts", "tests")
foreach ($dir in $includeDirs) {
    Copy-Item -LiteralPath (Join-Path $repoRoot $dir) -Destination $stagingRoot -Recurse -Force
}

$includeFiles = @(".gitignore", "README-CUDA.md")
foreach ($file in $includeFiles) {
    $source = Join-Path $repoRoot $file
    if (Test-Path $source) {
        Copy-Item -LiteralPath $source -Destination $stagingRoot -Force
    }
}

$cacheDirs = Get-ChildItem -LiteralPath $stagingRoot -Recurse -Directory -Force |
    Where-Object { $_.Name -in @("__pycache__", ".pytest_cache", ".venv", "node_modules", "dist", ".gradle", ".kotlin", "build") }
foreach ($cacheDir in $cacheDirs) {
    Remove-Item -LiteralPath $cacheDir.FullName -Recurse -Force
}

$compiledPythonFiles = Get-ChildItem -LiteralPath $stagingRoot -Recurse -File -Force -Include "*.pyc", "*.pyo"
foreach ($compiledPythonFile in $compiledPythonFiles) {
    Remove-Item -LiteralPath $compiledPythonFile.FullName -Force
}

$localPropertiesFiles = Get-ChildItem -LiteralPath $stagingRoot -Recurse -File -Force -Filter "local.properties"
foreach ($localPropertiesFile in $localPropertiesFiles) {
    Remove-Item -LiteralPath $localPropertiesFile.FullName -Force
}

if (Test-Path $archivePath) {
    Remove-Item -LiteralPath $archivePath -Force
}

Compress-Archive -Path (Join-Path $stagingRoot "*") -DestinationPath $archivePath -Force

Remove-Item -LiteralPath $stagingRoot -Recurse -Force

Write-Host "CUDA package created:"
Write-Host $archivePath
