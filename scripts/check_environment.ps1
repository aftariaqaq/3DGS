Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$checks = @(
    @{
        Name = "ffmpeg"
        Command = "ffmpeg"
        Arguments = @("-version")
    },
    @{
        Name = "colmap"
        Command = "colmap"
        Arguments = @("-h")
    },
    @{
        Name = "opensplat"
        Command = "opensplat.exe"
        Arguments = @("--help")
    }
)

$failed = $false

foreach ($check in $checks) {
    $command = [string]$check.Command
    $arguments = [string[]]$check.Arguments

    try {
        $executable = Get-Command $command -ErrorAction Stop
        $process = Start-Process `
            -FilePath $executable.Source `
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

