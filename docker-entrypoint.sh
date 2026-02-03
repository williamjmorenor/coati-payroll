#!/usr/bin/env sh
set -eu

PYTHON="/opt/venv/bin/python"
PAYROLLCTL="/opt/venv/bin/payrollctl"

if [ ! -x "$PYTHON" ]; then
  echo "[entrypoint] ERROR: python not found at $PYTHON"
  exit 1
fi

if [ ! -x "$PAYROLLCTL" ]; then
  echo "[entrypoint] ERROR: payrollctl not found at $PAYROLLCTL"
  exit 1
fi

echo "[entrypoint] Initializing database: payrollctl database init"
$PAYROLLCTL database init || true

echo "[entrypoint] Running migrations: payrollctl database migrate"
$PAYROLLCTL database migrate || true

echo "[entrypoint] Starting app: $*"
exec "$PYTHON" app.py