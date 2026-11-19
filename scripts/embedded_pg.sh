#!/usr/bin/env bash
# PostgreSQL local sem Docker e sem sudo, usando os binarios do pacote Python "pgserver".
# Uso: scripts/embedded_pg.sh start|stop|status
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PGBIN="$(ls -d "$ROOT"/backend/.venv/lib/python*/site-packages/pgserver/pginstall/bin | head -1)"
PGDATA="$ROOT/.pgdata"
PGPORT="${PGPORT:-5432}"
case "${1:-start}" in
  start)
    if [ ! -d "$PGDATA" ]; then
      echo "Inicializando cluster em $PGDATA"
      "$PGBIN/initdb" -D "$PGDATA" -U postgres --auth=trust -E UTF8 --locale=C >/dev/null
    fi
    if "$PGBIN/pg_ctl" -D "$PGDATA" status >/dev/null 2>&1; then echo "PostgreSQL ja esta em execucao"; else
      "$PGBIN/pg_ctl" -D "$PGDATA" -l "$ROOT/.pgdata.log" -o "-p $PGPORT -c listen_addresses=127.0.0.1 -k /tmp" -w start >/dev/null
      echo "PostgreSQL iniciado na porta $PGPORT"
    fi
    "$PGBIN/psql" -h 127.0.0.1 -p "$PGPORT" -U postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='finops'" | grep -q 1 || \
      "$PGBIN/psql" -h 127.0.0.1 -p "$PGPORT" -U postgres -c "CREATE ROLE finops LOGIN SUPERUSER PASSWORD 'finops'" >/dev/null
    "$PGBIN/psql" -h 127.0.0.1 -p "$PGPORT" -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='finops'" | grep -q 1 || \
      "$PGBIN/createdb" -h 127.0.0.1 -p "$PGPORT" -U postgres -O finops finops
    echo "DATABASE_URL=postgresql+psycopg://finops:finops@127.0.0.1:$PGPORT/finops"
    ;;
  stop) "$PGBIN/pg_ctl" -D "$PGDATA" -m fast stop ;;
  status) "$PGBIN/pg_ctl" -D "$PGDATA" status ;;
esac
