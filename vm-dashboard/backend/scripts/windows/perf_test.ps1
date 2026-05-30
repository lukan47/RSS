#Requires -RunAsAdministrator
<#
.SYNOPSIS
  Runs CPU, memory, disk, and network benchmarks on Windows Server.
  Uses built-in WinSAT for disk/CPU and PowerShell for memory/net.
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = 'SilentlyContinue'

Write-Output "=== SYSTEM INFO ==="
$os = Get-WmiObject Win32_OperatingSystem
$cpu = Get-WmiObject Win32_Processor
$mem = Get-WmiObject Win32_PhysicalMemory | Measure-Object Capacity -Sum
Write-Output "Hostname:   $($env:COMPUTERNAME)"
Write-Output "OS:         $($os.Caption)"
Write-Output "CPU:        $($cpu.Name)"
Write-Output "Cores:      $($cpu.NumberOfCores) cores / $($cpu.NumberOfLogicalProcessors) logical"
Write-Output "RAM:        $('{0:N1}' -f ($mem.Sum / 1GB)) GB"
Write-Output ""

Write-Output "=== CPU BENCHMARK (WinSAT) ==="
$cpuResult = winsat cpu 2>&1
$cpuResult | Where-Object { $_ -match "Score|CPU" } | ForEach-Object { Write-Output $_ }
Write-Output ""

Write-Output "=== MEMORY BENCHMARK ==="
# Simple PowerShell memory throughput test
$blockSizeMB = 256
$iterations = 10
$arr = New-Object byte[] ($blockSizeMB * 1MB)
$sw = [System.Diagnostics.Stopwatch]::StartNew()
for ($i = 0; $i -lt $iterations; $i++) {
    [System.Buffer]::BlockCopy($arr, 0, $arr, 0, $arr.Length)
}
$sw.Stop()
$totalMB = $blockSizeMB * $iterations
$throughput = [math]::Round($totalMB / ($sw.Elapsed.TotalSeconds), 1)
Write-Output "Memory copy throughput: $throughput MB/s ($totalMB MB in $([math]::Round($sw.Elapsed.TotalSeconds,2))s)"
Write-Output ""

Write-Output "=== DISK BENCHMARK (WinSAT) ==="
$diskResult = winsat disk 2>&1
$diskResult | Where-Object { $_ -match "Score|Disk|MB/s" } | ForEach-Object { Write-Output $_ }
Write-Output ""

Write-Output "=== NETWORK (loopback iperf3) ==="
$iperf = Get-Command iperf3 -ErrorAction SilentlyContinue
if ($iperf) {
    Start-Process iperf3 -ArgumentList "-s -p 15201 --one-off" -WindowStyle Hidden
    Start-Sleep -Seconds 1
    iperf3 -c 127.0.0.1 -p 15201 -t 10
} else {
    Write-Output "iperf3 not found — skipping network test (run prep script first)"
}
Write-Output ""

Write-Output "=== ALL TESTS COMPLETE ==="
