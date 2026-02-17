#!/usr/bin/env sh
set -eu

PYTHON="/opt/venv/bin/python"
PAYROLLCTL="/opt/venv/bin/payrollctl"
DRAMATIQ="/opt/venv/bin/dramatiq"

is_true() {
  case "${1:-}" in
    1|true|TRUE|True|yes|YES|on|ON)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

if [ ! -x "$PYTHON" ]; then
  echo "[entrypoint] ERROR: python not found at $PYTHON"
  exit 1
fi

if [ ! -x "$PAYROLLCTL" ]; then
  echo "[entrypoint] ERROR: payrollctl not found at $PAYROLLCTL"
  exit 1
fi

if [ ! -x "$DRAMATIQ" ]; then
  echo "[entrypoint] ERROR: dramatiq not found at $DRAMATIQ"
  exit 1
fi

echo "[entrypoint] Initializing database: payrollctl database init"
$PAYROLLCTL database init || true

echo "[entrypoint] Running migrations: payrollctl database migrate"
$PAYROLLCTL database migrate || true

# Start Dramatiq worker in background when queue is enabled and Redis is configured.
# This is the minimal operational setup so enqueued payroll jobs are processed.
QUEUE_ENABLED="${QUEUE_ENABLED:-1}"
REDIS_URL="${REDIS_URL:-${CACHE_REDIS_URL:-}}"
WORKER_THREADS="${DRAMATIQ_WORKER_THREADS:-8}"
WORKER_PROCESSES="${DRAMATIQ_WORKER_PROCESSES:-2}"

if is_true "$QUEUE_ENABLED" && [ -n "$REDIS_URL" ]; then
  echo "[entrypoint] Starting Dramatiq worker (threads=$WORKER_THREADS, processes=$WORKER_PROCESSES)"
  "$DRAMATIQ" coati_payroll.queue.tasks --threads "$WORKER_THREADS" --processes "$WORKER_PROCESSES" &
else
  echo "[entrypoint] Dramatiq worker not started (QUEUE_ENABLED=$QUEUE_ENABLED, REDIS_URL configured=$([ -n "$REDIS_URL" ] && echo yes || echo no))"
fi

echo "[entrypoint] Starting app: $*"
exec "$PYTHON" app.py