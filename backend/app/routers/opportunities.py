from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..db import execute, q, q1
from ..seed.catalog import OPP_TYPE_NAME, OPP_TYPES
from ..services.common import org_id, pct

router = APIRouter(prefix="/api/opportunities", tags=["finops-opportunities"])
STATUSES = ["Identificada", "Em análise", "Aprovada", "Em execução", "Capturada"]
TYPE_DESC = {t[0]: t[5] for t in OPP_TYPES}
LEVEL = {1: "Baixo", 2: "Médio", 3: "Alto"}


def _where(company, cloud, typ, status, effort, risk, open_only=False, search=None):
    w, p = ["org_id=:o"], {"o": org_id()}
    if open_only:
        w.append("status <> 'Capturada'")
    for col, val, key in (("company_code", company, "co"), ("cloud_code", cloud, "cl"), ("opp_type", typ, "ty"),
                          ("status", status, "st"), ("effort", effort, "ef"), ("risk", risk, "rk")):
        if val:
            w.append(f"{col}=:{key}")
            p[key] = val
    if search:
        w.append("(title ILIKE :s OR resource_name ILIKE :s)")
        p["s"] = f"%{search}%"
    return " AND ".join(w), p


@router.get("/summary")
def summary(company: str | None = None, cloud: str | None = None):
    where, p = _where(company, cloud, None, None, None, None, open_only=True)
    rows = q(f"""SELECT opp_type, COUNT(*) AS n, SUM(savings_monthly_brl) AS savings, SUM(current_cost_brl) AS cost,
                        AVG(term_days) AS term_days,
                        SUM(priority_score*savings_monthly_brl)/NULLIF(SUM(savings_monthly_brl),0) AS score,
                        SUM(CASE effort WHEN 'Baixo' THEN 1 WHEN 'Médio' THEN 2 ELSE 3 END*savings_monthly_brl)/NULLIF(SUM(savings_monthly_brl),0) AS effort_idx,
                        SUM(CASE risk WHEN 'Baixo' THEN 1 WHEN 'Médio' THEN 2 ELSE 3 END*savings_monthly_brl)/NULLIF(SUM(savings_monthly_brl),0) AS risk_idx
                 FROM v_opportunity WHERE {where} GROUP BY 1 ORDER BY savings DESC""", **p)
    cap_where, cp = _where(company, cloud, None, None, None, None)
    captured = {r["opp_type"]: r["s"] for r in q(
        f"SELECT opp_type, SUM(savings_monthly_brl) AS s FROM v_opportunity WHERE {cap_where} AND status='Capturada' GROUP BY 1", **cp)}
    total_cost = q1("SELECT SUM(cost_brl) AS c FROM v_cost WHERE org_id=:o AND month=(SELECT max(month) FROM cost_monthly)"
                    + (" AND company_code=:co" if company else "") + (" AND cloud_code=:cl" if cloud else ""),
                    o=org_id(), co=company, cl=cloud)["c"] or 1
    items = []
    for r in rows:
        items.append({"type": r["opp_type"], "name": OPP_TYPE_NAME[r["opp_type"]], "description": TYPE_DESC[r["opp_type"]],
                      "count": r["n"], "savings_monthly": round(r["savings"], 2), "savings_annual": round(r["savings"] * 12, 2),
                      "savings_pct": pct(r["savings"], r["cost"]), "addressable_cost": round(r["cost"], 2),
                      "pct_of_total_spend": pct(r["savings"], total_cost), "term_days": round(r["term_days"]),
                      "effort_idx": round(r["effort_idx"], 2), "effort": LEVEL[round(r["effort_idx"])],
                      "risk_idx": round(r["risk_idx"], 2), "risk": LEVEL[round(r["risk_idx"])],
                      "score": round(r["score"], 1), "captured_monthly": round(captured.get(r["opp_type"], 0) or 0, 2)})
    order = sorted(items, key=lambda x: -x["score"])
    n1, n2 = max(1, round(len(order) * 0.3)), max(1, round(len(order) * 0.7))
    for i, it in enumerate(order):
        it["priority"] = "P1" if i < n1 else "P2" if i < n2 else "P3"
        it["rank"] = i + 1
    by_status = q(f"SELECT status, COUNT(*) AS n, SUM(savings_monthly_brl) AS s FROM v_opportunity WHERE {cap_where} GROUP BY 1", **cp)
    by_company = q(f"""SELECT company_code AS code, company_name AS name, SUM(savings_monthly_brl) AS savings FROM v_opportunity
                       WHERE {where} GROUP BY 1,2 ORDER BY 3 DESC""", **p)
    by_cloud = q(f"SELECT cloud_code AS code, cloud_name AS name, SUM(savings_monthly_brl) AS savings FROM v_opportunity WHERE {where} GROUP BY 1,2 ORDER BY 3 DESC", **p)
    tot = sum(i["savings_monthly"] for i in items)
    return {"types": order, "total_monthly": round(tot, 2), "total_annual": round(tot * 12, 2),
            "pct_of_spend": pct(tot, total_cost), "captured_monthly": round(sum(captured.values()), 2),
            "by_status": [{"status": s, "count": next((x["n"] for x in by_status if x["status"] == s), 0),
                           "savings": round(next((x["s"] for x in by_status if x["status"] == s), 0) or 0, 2)} for s in STATUSES],
            "by_company": by_company, "by_cloud": by_cloud}


SORTS = {"savings": "savings_monthly_brl", "score": "priority_score", "pct": "savings_pct", "term": "term_days", "company": "company_name"}


@router.get("")
def listing(company: str | None = None, cloud: str | None = None, type: str | None = None, status: str | None = None,
            effort: str | None = None, risk: str | None = None, open_only: bool = True, q_: str | None = Query(None, alias="q"),
            sort: str = "savings", dir: str = "desc", page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200)):
    where, p = _where(company, cloud, type, status, effort, risk, open_only, q_)
    total = q1(f"SELECT COUNT(*) AS n, COALESCE(SUM(savings_monthly_brl),0) AS s FROM v_opportunity WHERE {where}", **p)
    col = SORTS.get(sort, "savings_monthly_brl")
    d = "ASC" if dir.lower() == "asc" else "DESC"
    rows = q(f"""SELECT id, company_code, company_name, cloud_code, opp_type, title, description, resource_name, service,
                        current_cost_brl, savings_monthly_brl, savings_pct, effort, term_days, risk, priority_score, status, owner
                 FROM v_opportunity WHERE {where} ORDER BY {col} {d}, id LIMIT :lim OFFSET :off""",
             **p, lim=page_size, off=(page - 1) * page_size)
    for r in rows:
        r["type_name"] = OPP_TYPE_NAME[r["opp_type"]]
    return {"total": total["n"], "savings_monthly": round(total["s"], 2), "page": page, "page_size": page_size, "rows": rows}


class StatusBody(BaseModel):
    status: str = Field(pattern="^(Identificada|Em análise|Aprovada|Em execução|Capturada)$")


@router.patch("/{opp_id}")
def update_status(opp_id: int, body: StatusBody):
    if not q1("SELECT 1 AS x FROM v_opportunity WHERE id=:i AND org_id=:o", i=opp_id, o=org_id()):
        raise HTTPException(404, "Oportunidade não encontrada")
    execute("UPDATE opportunity SET status=:s WHERE id=:i", s=body.status, i=opp_id)
    return {"ok": True, "status": body.status}
