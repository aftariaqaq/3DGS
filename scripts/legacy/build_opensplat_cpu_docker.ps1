Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$dockerfile = Join-Path $repoRoot "docker\legacy\opensplat-cpu.Dockerfile"

docker build `
    -f $dockerfile `
    -t opensplat-cpu:local `
    $repoRoot
