#!/bin/sh
set -eu

cd /app

# Initialize demo data only when the database has no schema yet.
if [ "$(python -c "from app.db import scalar; print(scalar(\"select to_regclass('public.org') is not null\"))" 2>/dev/null || true)" != "True" ]; then
  python -m app.seed
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
