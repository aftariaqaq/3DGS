param(
    [string]$ImageName = "3dgs-runtime:rtx5090",
    [string]$TarPath = "artifacts\3dgs-runtime-rtx5090.tar",
    [string]$UbuntuMirror = "https://mirrors.aliyun.com/ubuntu",
    [string]$PipIndexUrl = "https://mirrors.aliyun.com/pypi/simple",
    [string]$PipTrustedHost = "mirrors.aliyun.com",
    [string]$ColmapRepository = "https://github.com/colmap/colmap.git",
    [switch]$NoSave
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$dockerfile = Join-Path $repoRoot "docker\nerfstudio-splatfacto.Dockerfile"
$docker = (Get-Command "docker" -ErrorAction Stop).Source

$proxyVars = @(
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "FTP_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "ftp_proxy"
)
foreach ($name in $proxyVars) {
    Remove-Item "Env:$name" -ErrorAction SilentlyContinue
}

& $docker build `
    --progress plain `
    --build-arg "UBUNTU_MIRROR=$UbuntuMirror" `
    --build-arg "PIP_INDEX_URL=$PipIndexUrl" `
    --build-arg "PIP_TRUSTED_HOST=$PipTrustedHost" `
    --build-arg "COLMAP_REPOSITORY=$ColmapRepository" `
    --build-arg "HTTP_PROXY=" `
    --build-arg "HTTPS_PROXY=" `
    --build-arg "ALL_PROXY=" `
    --build-arg "FTP_PROXY=" `
    --build-arg "http_proxy=" `
    --build-arg "https_proxy=" `
    --build-arg "all_proxy=" `
    --build-arg "ftp_proxy=" `
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
