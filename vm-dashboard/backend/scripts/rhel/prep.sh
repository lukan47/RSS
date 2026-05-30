#!/bin/bash
set -euo pipefail

echo "=== RHEL/CentOS Performance Test Prep ==="

# Package manager: prefer dnf, fall back to yum
PKG=$(command -v dnf 2>/dev/null || command -v yum)

echo "Installing EPEL repository..."
$PKG install -y epel-release 2>/dev/null || true

echo "Installing performance testing tools..."
$PKG install -y \
    sysbench \
    fio \
    iperf3 \
    stress-ng \
    sysstat \
    htop \
    numactl \
    lshw \
    util-linux

echo "Disabling tuned power-saving profiles for accurate benchmarks..."
systemctl stop tuned 2>/dev/null || true
systemctl disable tuned 2>/dev/null || true

echo "Setting CPU governor to performance..."
if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo performance > "$gov" 2>/dev/null || true
    done
fi

echo "Disabling swap for memory tests..."
swapoff -a 2>/dev/null || true

echo "=== Prep complete ==="
