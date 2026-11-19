"""ETL: coleta via conector, normaliza e grava no modelo unificado. Modo demo apenas registra a execucao."""
from __future__ import annotations

from datetime import date, datetime, timezone

from ..connectors.factory import get_connector
from ..db import engine, q1
from ..security import decrypt
from ..services.common import add_months
from sqlalchemy import text


def _finish(conn_id: int, run_id: int, status: str, msg: str, costs=0, res=0, recs=0):
    with engine.begin() as c:
        c.execute(text("UPDATE etl_run SET finished_at=now(), status=:s, message=:m, rows_cost=:a, rows_resources=:b, rows_recs=:r WHERE id=:i"),
                  dict(s=status, m=msg, a=costs, b=res, r=recs, i=run_id))
        c.execute(text("UPDATE cloud_connection SET last_sync_at=now(), status=:s, last_message=:m WHERE id=:i"),
                  dict(s="connected" if status == "success" else "error", m=msg, i=conn_id))


def sync_connection(conn_id: int) -> dict:
    row = q1("SELECT * FROM cloud_connection WHERE id=:i", i=conn_id)
    with engine.begin() as c:
        run_id = c.execute(text("INSERT INTO etl_run (connection_id, status) VALUES (:i,'running') RETURNING id"), dict(i=conn_id)).scalar()
    if row["mode"] == "demo":
        n = q1("""SELECT COUNT(*) AS n FROM cost_monthly cm JOIN resource r ON r.id=cm.resource_id
                  WHERE r.company_id=:c AND r.cloud_code=:cl""", c=row["company_id"], cl=row["cloud_code"])["n"]
        k = q1("SELECT COUNT(*) AS n FROM resource WHERE company_id=:c AND cloud_code=:cl", c=row["company_id"], cl=row["cloud_code"])["n"]
        _finish(conn_id, run_id, "success", "Sincronização de demonstração (dados simulados já carregados)", n, k, 0)
        return {"status": "success", "mode": "demo", "rows_cost": n, "rows_resources": k}
    try:
        conn = get_connector(row["cloud_code"], row["config"], decrypt(row["secret_enc"]))
        end = date.today().replace(day=1)
        costs = conn.fetch_costs(add_months(end, -12), end)
        resources, recs = conn.fetch_resources(), conn.fetch_recommendations()
        loaded = load_costs(row, costs, float(row["config"].get("fx_usd_brl", 5.0)))
        _finish(conn_id, run_id, "success", f"Coleta concluída: {len(costs)} linhas de custo", loaded, len(resources), len(recs))
        return {"status": "success", "mode": "live", "rows_cost": loaded, "rows_resources": len(resources), "rows_recs": len(recs)}
    except Exception as e:  # erro de credencial, SDK ausente, API indisponivel...
        _finish(conn_id, run_id, "error", str(e)[:300])
        return {"status": "error", "message": str(e)[:300]}


def load_costs(conn: dict, costs: list[dict], fx: float) -> int:
    """Grava custos coletados como recursos agregados (conta x servico) para aparecerem nos dashboards."""
    n = 0
    with engine.begin() as c:
        for r in costs:
            amt = r["cost"] * (fx if r["currency"] == "USD" else 1.0)
            acc = c.execute(text("SELECT id FROM cloud_account WHERE company_id=:c AND cloud_code=:cl AND external_id=:e"),
                            dict(c=conn["company_id"], cl=conn["cloud_code"], e=r["account"])).scalar()
            if acc is None:
                acc = c.execute(text("""INSERT INTO cloud_account (company_id, cloud_code, external_id, name, env_scope)
                                        VALUES (:c,:cl,:e,:e,'prod') RETURNING id"""),
                                dict(c=conn["company_id"], cl=conn["cloud_code"], e=r["account"])).scalar()
            name = f"{r['service']} (agregado)"
            rid = c.execute(text("SELECT id FROM resource WHERE account_id=:a AND resource_name=:n"), dict(a=acc, n=name)).scalar()
            if rid is None:
                rid = c.execute(text("""INSERT INTO resource (account_id, company_id, cloud_code, service, resource_type, resource_name, tags)
                                        VALUES (:a,:c,:cl,:s,'aggregate',:n,CAST(:t AS jsonb)) RETURNING id"""),
                                dict(a=acc, c=conn["company_id"], cl=conn["cloud_code"], s=r["service"], n=name,
                                     t=__import__("json").dumps(r["tags"]))).scalar()
            c.execute(text("""INSERT INTO cost_monthly (resource_id, month, cost_brl) VALUES (:r,:m,:v)
                              ON CONFLICT (resource_id, month) DO UPDATE SET cost_brl=EXCLUDED.cost_brl"""),
                      dict(r=rid, m=r["month"], v=round(amt, 2)))
            n += 1
    return n
