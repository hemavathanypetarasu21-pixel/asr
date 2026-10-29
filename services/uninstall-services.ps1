#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Stops and removes the ASR Studio Windows services. Logs in services\logs are kept.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File D:\asr\services\uninstall-services.ps1
#>
param(
    [string]$BackendServiceName = "ASRStudioBackend",
    [string]$FrontendServiceName = "ASRStudioFrontend"
)

$ErrorActionPreference = "Stop"
$Nssm = Join-Path $PSScriptRoot "bin\nssm.exe"
if (-not (Test-Path $Nssm)) { throw "NSSM not found at $Nssm; the services were not installed by install-services.ps1." }

# Frontend first: it depends on the backend.
foreach ($name in $FrontendServiceName, $BackendServiceName) {
    if (-not (Get-Service -Name $name -ErrorAction SilentlyContinue)) {
        Write-Host "$name is not installed."
        continue
    }
    Stop-Service -Name $name -Force -ErrorAction SilentlyContinue
    & $Nssm remove $name confirm
    if ($LASTEXITCODE -ne 0) { throw "Could not remove $name (exit code $LASTEXITCODE)." }
    Write-Host "Removed $name."
}
