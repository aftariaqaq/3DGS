param(
    [string]$ImageName = "3dgs-runtime:rtx5090",
    [string]$TarPath = "artifacts\3dgs-runtime-rtx5090.tar",
    [switch]$NoSave
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$dockerfile = Join-Path $repoRoot "docker\nerfstudio-splatfacto.Dockerfile"
$docker = (Get-Command "docker" -ErrorAction Stop).Source

& $docker build `
    -f $dockerfile `
    -t $ImageName `
    $repoRoot
if ($LASTEXITCODE -ne 0) {
    throw "Docker build failed with exit code $LASTEXITCODE"
}

if (!$NoSave) {
    $resolvedTarPath = Join-Path $repoRoot $TarPath
    New-Item -ItemType Directory -Force -Path (Split-Path $resolvedTarPath -Parent) | Out-Null
    if (Test-Path $resolvedTarPath) {
        Remove-Item -LiteralPath $resolvedTarPath -Force
    }
    & $docker save -o $resolvedTarPath $ImageName
    if ($LASTEXITCODE -ne 0) {
        throw "Docker save failed with exit code $LASTEXITCODE"
    }
    Write-Host "Runtime image archive created:"
    Write-Host $resolvedTarPath
}
