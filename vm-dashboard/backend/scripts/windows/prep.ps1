#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Installs performance testing tools on Windows Server via Chocolatey.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Output "=== Windows Performance Test Prep ==="

# Install Chocolatey if not present
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Output "Installing Chocolatey..."
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    $env:PATH += ";$env:ProgramData\chocolatey\bin"
}

Write-Output "Installing iperf3..."
choco install -y iperf3

Write-Output "Setting power plan to High Performance..."
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c

Write-Output "Disabling CPU throttling (Windows power settings)..."
powercfg /change monitor-timeout-ac 0
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0

Write-Output "Ensuring temp directory exists..."
New-Item -ItemType Directory -Force -Path "C:\Temp" | Out-Null

Write-Output "=== Prep complete ==="
