#!/bin/bash
set -euo pipefail

echo "=== Ubuntu/Debian Performance Test Prep ==="

export DEBIAN_FRONTEND=noninteractive

echo "Updating package lists..."
apt-get update -y

echo "Installing performance testing tools..."
apt-get install -y \
    sysbench \
    fio \
    iperf3 \
    stress-ng \
    sysstat \
    htop \
    numactl \
    lshw \
    linux-tools-common \
    linux-tools-generic \
    util-linux

echo "Disabling power-saving CPU scaling..."
if command -v cpupower &>/dev/null; then
    cpupower frequency-set -g performance 2>/dev/null || true
else
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo performance > "$gov" 2>/dev/null || true
    done
fi

echo "Disabling swap for memory tests..."
swapoff -a 2>/dev/null || true

echo "=== Prep complete ==="
