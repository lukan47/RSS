#!/bin/bash
set -euo pipefail

THREADS=$(nproc)
RESULTS_FILE="/tmp/perf_results.json"

echo "=== SYSTEM INFO ==="
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -r)"
lscpu | grep -E "Model name|Socket|Core|Thread|CPU\(s\):"
free -h
df -h / | tail -1

echo ""
echo "=== CPU BENCHMARK (sysbench, ${THREADS} threads, 30s) ==="
sysbench cpu --threads="$THREADS" --time=30 run

echo ""
echo "=== MEMORY BENCHMARK (sysbench, sequential write, 30s) ==="
sysbench memory --memory-block-size=1M --memory-total-size=100G \
    --memory-access-mode=seq --memory-oper=write --threads="$THREADS" --time=30 run

echo ""
echo "=== DISK I/O BENCHMARK (fio, 4K random read/write, 30s) ==="
fio --name=randrw --ioengine=libaio --iodepth=16 \
    --rw=randrw --bs=4k --direct=1 --size=512m \
    --numjobs="$THREADS" --runtime=30 --time_based \
    --filename=/tmp/fio_test.bin --output-format=normal \
    --group_reporting
rm -f /tmp/fio_test.bin

echo ""
echo "=== NETWORK (localhost iperf3 loopback) ==="
iperf3 -s -D -p 15201 --one-off 2>/dev/null &
sleep 1
iperf3 -c 127.0.0.1 -p 15201 -t 10 || true
kill %1 2>/dev/null || true

echo ""
echo "=== ALL TESTS COMPLETE ==="
