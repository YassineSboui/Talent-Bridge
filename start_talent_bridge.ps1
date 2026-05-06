param(
    [switch]$SkipSql,
    [switch]$SkipDashboard,
    [switch]$SkipBrowser,
    [switch]$NoInstall,
    [switch]$RunChecks
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Launcher = Join-Path $Root "Infrastructure\scripts\start_local.ps1"

if (-not (Test-Path -LiteralPath $Launcher)) {
    throw "Launcher not found: $Launcher"
}

& $Launcher @PSBoundParameters
