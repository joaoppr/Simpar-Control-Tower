#!/usr/bin/env bash
# Sobe tudo para a demo local: PostgreSQL embarcado, dados fictícios (se vazio), build do frontend e API em http://localhost:8888
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$HOME/.local/node/bin:$PATH"
cd "$ROOT/backend"
[ -d .venv ] || { python3 -m venv --without-pip .venv && curl -sS https://bootstrap.pypa.io/get-pip.py | .venv/bin/python -q; }
.venv/bin/pip install -q -r requirements-dev.txt
"$ROOT/scripts/embedded_pg.sh" start
if [ "$(.venv/bin/python -c "from app.db import scalar; print(scalar(\"select to_regclass('public.org') is not null\"))" 2>/dev/null)" != "True" ]; then
  .venv/bin/python -m app.seed
fi
cd "$ROOT/frontend"
[ -x node_modules/.bin/vite ] || npm install
[ -d dist ] || npm run build
cd "$ROOT/backend"
echo "Abra http://localhost:8888"
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8888
