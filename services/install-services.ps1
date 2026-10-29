#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Installs ASR Studio as two Windows services (backend + frontend) using NSSM.

.DESCRIPTION
    - Backend:  python backend\server.py   (host/port from backend\.env, auto-reload off)
    - Frontend: next start (production build of frontend\, built by this script)
    Both start automatically with Windows, restart on failure, and log to services\logs.
    Re-running the script reinstalls the services with the current settings.

.EXAMPLE
    # From an elevated PowerShell:
    powershell -ExecutionPolicy Bypass -File D:\asr\services\install-services.ps1
#>
param(
    [string]$BackendServiceName = "ASRStudioBackend",
    [string]$FrontendServiceName = "ASRStudioFrontend",
    [int]$FrontendPort = 3000,
    [string]$FrontendHost = "127.0.0.1",
    # Skip "pnpm install" + "pnpm build" (use the existing frontend\.next build).
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$ServicesDir = $PSScriptRoot
$Root = Split-Path -Parent $ServicesDir
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$LogsDir = Join-Path $ServicesDir "logs"
$BinDir = Join-Path $ServicesDir "bin"
$Nssm = Join-Path $BinDir "nssm.exe"
$LogRotateBytes = 10MB
$RestartDelayMs = 5000

function Write-Step([string]$Message) { Write-Host "==> $Message" -ForegroundColor Cyan }

function Resolve-Tool([string]$Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) { throw "'$Name' was not found on PATH. Install it and run this script again." }
    return $command.Source
}

function Read-DotEnv([string]$Path) {
    $values = @{}
    foreach ($line in Get-Content $Path) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') { $values[$Matches[1]] = $Matches[2].Trim() }
    }
    return $values
}

function Assert-PortFree([int]$Port) {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $listener) { return }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)" -ErrorAction SilentlyContinue
    throw "Port $Port is already in use by PID $($listener.OwningProcess) ($($process.CommandLine)). Stop it (e.g. a dev server) and run this script again."
}

function Install-Nssm {
    if (Test-Path $Nssm) { return }
    New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    $found = Get-Command nssm -ErrorAction SilentlyContinue
    if (-not $found) {
        Write-Step "Installing NSSM with winget"
        winget install --id NSSM.NSSM --source winget --exact --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
        $roots = @("$env:LOCALAPPDATA\Microsoft\WinGet\Packages", "$env:ProgramFiles\WinGet\Packages")
        $found = Get-ChildItem -Path $roots -Recurse -Filter nssm.exe -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match 'win64' } | Select-Object -First 1
        if (-not $found) { throw "NSSM could not be installed. Download it from https://nssm.cc and place nssm.exe in $BinDir." }
        $found = $found.FullName
    } else {
        $found = $found.Source
    }
    # Keep a copy next to the scripts so the services never depend on a per-user install path.
    Copy-Item $found $Nssm -Force
}

function Invoke-Nssm {
    & $Nssm @args
    if ($LASTEXITCODE -ne 0) { throw "nssm $($args -join ' ') failed with exit code $LASTEXITCODE" }
}

function Install-AppService {
    param(
        [string]$Name, [string]$DisplayName, [string]$Description,
        [string]$Executable, [string]$Arguments, [string]$WorkingDirectory,
        [string[]]$Environment, [string]$LogFile, [string[]]$DependsOn
    )
    if (Get-Service -Name $Name -ErrorAction SilentlyContinue) {
        Write-Step "Removing existing service $Name"
        Stop-Service -Name $Name -Force -ErrorAction SilentlyContinue
        Invoke-Nssm remove $Name confirm
    }
    Write-Step "Installing service $Name"
    Invoke-Nssm install $Name $Executable $Arguments
    Invoke-Nssm set $Name AppDirectory $WorkingDirectory
    Invoke-Nssm set $Name DisplayName $DisplayName
    Invoke-Nssm set $Name Description $Description
    Invoke-Nssm set $Name Start SERVICE_AUTO_START
    Invoke-Nssm set $Name AppStdout $LogFile
    Invoke-Nssm set $Name AppStderr $LogFile
    Invoke-Nssm set $Name AppRotateFiles 1
    Invoke-Nssm set $Name AppRotateOnline 1
    Invoke-Nssm set $Name AppRotateBytes $LogRotateBytes
    Invoke-Nssm set $Name AppExit Default Restart
    Invoke-Nssm set $Name AppRestartDelay $RestartDelayMs
    Invoke-Nssm set $Name AppEnvironmentExtra @Environment
    if ($DependsOn) { Invoke-Nssm set $Name DependOnService @DependsOn }
    Start-Service -Name $Name
}

# --- Resolve tools and settings -------------------------------------------------------------

Write-Step "Resolving tools"
$Python = Resolve-Tool "python"
$Node = Resolve-Tool "node"
$Ffmpeg = Resolve-Tool "ffmpeg"
$Ffprobe = Resolve-Tool "ffprobe"
# Services run as LocalSystem, which does not see this user's site-packages or Whisper cache.
$UserSitePackages = (& $Python -c "import site; print(site.getusersitepackages())").Trim()
$CacheHome = Join-Path $env:USERPROFILE ".cache"

$BackendEnvFile = Join-Path $BackendDir ".env"
$FrontendEnvFile = Join-Path $FrontendDir ".env.local"
foreach ($file in $BackendEnvFile, $FrontendEnvFile) {
    if (-not (Test-Path $file)) { throw "$file is missing. Create it from the matching .env.example first." }
}
$BackendEnv = Read-DotEnv $BackendEnvFile
$BackendPort = [int]$BackendEnv["SERVER_PORT"]

# Stop a previous install first so its own processes do not count as "port in use".
foreach ($name in $FrontendServiceName, $BackendServiceName) {
    Stop-Service -Name $name -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2
Assert-PortFree -Port $BackendPort
Assert-PortFree -Port $FrontendPort

New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null
Install-Nssm

# --- Frontend production build --------------------------------------------------------------

if (-not $SkipBuild) {
    Write-Step "Building the frontend (pnpm install + pnpm build)"
    Push-Location $FrontendDir
    try {
        pnpm install --frozen-lockfile
        if ($LASTEXITCODE -ne 0) { throw "pnpm install failed." }
        pnpm build
        if ($LASTEXITCODE -ne 0) { throw "pnpm build failed." }
    } finally {
        Pop-Location
    }
}
$NextCli = Join-Path $FrontendDir "node_modules\next\dist\bin\next"
if (-not (Test-Path $NextCli)) { throw "Next.js was not found at $NextCli. Run without -SkipBuild." }

# --- Services -------------------------------------------------------------------------------

$MongoDependency = @()
if (Get-Service -Name "MongoDB" -ErrorAction SilentlyContinue) { $MongoDependency = @("MongoDB") }

Install-AppService `
    -Name $BackendServiceName `
    -DisplayName "ASR Studio Backend" `
    -Description "ASR Studio FastAPI backend (Whisper, MongoDB, Gemini). Runs backend\server.py." `
    -Executable $Python `
    -Arguments "`"$(Join-Path $BackendDir 'server.py')`"" `
    -WorkingDirectory $BackendDir `
    -Environment @(
        "SERVER_RELOAD=false",
        "PYTHONUNBUFFERED=1",
        "PYTHONPATH=$UserSitePackages",
        "XDG_CACHE_HOME=$CacheHome",
        "FFMPEG_BINARY=$Ffmpeg",
        "FFPROBE_BINARY=$Ffprobe"
    ) `
    -LogFile (Join-Path $LogsDir "backend.log") `
    -DependsOn $MongoDependency

Install-AppService `
    -Name $FrontendServiceName `
    -DisplayName "ASR Studio Frontend" `
    -Description "ASR Studio Next.js frontend (production build, next start)." `
    -Executable $Node `
    -Arguments "`"$NextCli`" start --port $FrontendPort --hostname $FrontendHost" `
    -WorkingDirectory $FrontendDir `
    -Environment @("NODE_ENV=production") `
    -LogFile (Join-Path $LogsDir "frontend.log") `
    -DependsOn @($BackendServiceName)

Write-Host ""
Get-Service $BackendServiceName, $FrontendServiceName | Format-Table Name, Status, StartType -AutoSize
Write-Host "Frontend: http://localhost:$FrontendPort"
Write-Host "Backend:  http://localhost:$BackendPort/health"
Write-Host "Logs:     $LogsDir"
