param(
    [string]$ImageName = "opensplat-cuda:local",
    [string]$CudaVersion = "12.1.1",
    [string]$TorchVersion = "2.2.1",
    [string]$CudaArchitectures = "75;80;86;89"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$dockerfile = Join-Path $repoRoot "docker\opensplat-cuda.Dockerfile"

docker build `
    -f $dockerfile `
    -t $ImageName `
    --build-arg "CUDA_VERSION=$CudaVersion" `
    --build-arg "TORCH_VERSION=$TorchVersion" `
    --build-arg "CMAKE_CUDA_ARCHITECTURES=$CudaArchitectures" `
    $repoRoot
