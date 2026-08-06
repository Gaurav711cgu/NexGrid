#!/usr/bin/env bash
# NexaGrid Performance & Load Benchmark Suite
# Target: 200 Concurrent Virtual Users (VUs) for FAANG Production Profile

set -e

HOST=${1:-"http://localhost:8000"}
USERS=${2:-200}
SPAWN_RATE=${3:-10}
RUN_TIME=${4:-"60s"}
OUTPUT_DIR="benchmarks/results"

mkdir -p "$OUTPUT_DIR"

echo "=========================================================="
echo " Starting NexaGrid Benchmark Suite"
echo " Target: $USERS Virtual Users @ $HOST"
echo " Duration: $RUN_TIME"
echo " Output: $OUTPUT_DIR/locust_report_${USERS}vu.html"
echo "=========================================================="

locust -f backend/tests/load/locustfile.py \
  --host="$HOST" \
  --users "$USERS" \
  --spawn-rate "$SPAWN_RATE" \
  --run-time "$RUN_TIME" \
  --headless \
  --html "$OUTPUT_DIR/locust_report_${USERS}vu.html" \
  --csv "$OUTPUT_DIR/locust_summary_${USERS}vu"

echo "Benchmark run complete! Results written to $OUTPUT_DIR/"
