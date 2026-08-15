#!/usr/bin/env bash
# Container entrypoint: wait for Postgres, apply migrations, optionally seed,
# then exec the given command (uvicorn by default).
set -euo pipefail

wait_for_db() {
  python - <<'PY'
import os, socket, sys
host = os.environ.get("POSTGRES_HOST", "postgres")
port = int(os.environ.get("POSTGRES_PORT", "5432"))
s = socket.socket()
s.settimeout(1)
try:
    s.connect((host, port))
    s.close()
except OSError:
    sys.exit(1)
PY
}

echo "[entrypoint] waiting for postgres ..."
for i in $(seq 1 60); do
  if wait_for_db; then
    echo "[entrypoint] postgres is reachable."
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "[entrypoint] ERROR: postgres not reachable after 60s" >&2
    exit 1
  fi
  sleep 1
done

echo "[entrypoint] applying database migrations ..."
alembic upgrade head

if [ "${SEED_ON_START:-false}" = "true" ]; then
  echo "[entrypoint] seeding database (sources + games + sample articles) ..."
  python -m app.seed || echo "[entrypoint] seed step reported an issue (continuing)."
fi

echo "[entrypoint] starting: $*"
exec "$@"
