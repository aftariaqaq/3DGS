Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
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

    return $null
}

$checks = @(
    @{
        Name = "ffmpeg"
        Command = "ffmpeg"
        Arguments = @("-version")
        FallbackPaths = @(
            "C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe"
        )
    },
    @{
        Name = "colmap"
        Command = "colmap"
        Arguments = @("-h")
        FallbackPaths = @(
            "$localToolsRoot\colmap-x64-windows-cuda\bin\colmap.exe"
            "$localToolsRoot\colmap-x64-windows-nocuda\bin\colmap.exe"
        )
    },
    @{
        Name = "opensplat"
        Command = "opensplat.exe"
        Arguments = @("--help")
        FallbackPaths = @(
            "$repoRoot\tools\opensplat\opensplat.exe",
            "$localToolsRoot\opensplat\opensplat.exe"
        )
        DockerImage = "opensplat-cuda:local"
    }
)

$failed = $false

foreach ($check in $checks) {
    $command = [string]$check.Command
    $arguments = [string[]]$check.Arguments
    $fallbackPaths = [string[]]$check.FallbackPaths

    try {
        $executable = Find-Executable -Command $command -FallbackPaths $fallbackPaths
        if (-not $executable) {
            if ($check.ContainsKey("DockerImage")) {
                $imageName = [string]$check.DockerImage
                $dockerImageId = docker image ls $imageName --quiet 2>$null
                if ($LASTEXITCODE -eq 0 -and $dockerImageId) {
                    Write-Host "[OK] $($check.Name) via Docker image $imageName"
                    continue
                }
            }

            throw "Executable not found"
        }

        $process = Start-Process `
            -FilePath $executable `
            -ArgumentList $arguments `
            -NoNewWindow `
            -Wait `
            -PassThru `
            -RedirectStandardOutput ([System.IO.Path]::GetTempFileName()) `
            -RedirectStandardError ([System.IO.Path]::GetTempFileName())

        if ($process.ExitCode -eq 0) {
            Write-Host "[OK] $($check.Name)"
        }
        else {
            Write-Host "[FAIL] $($check.Name) exited with code $($process.ExitCode)"
            $failed = $true
        }
    }
    catch {
        Write-Host "[FAIL] $($check.Name) not found or not executable"
        $failed = $true
    }
}

if ($failed) {
    exit 1
}
