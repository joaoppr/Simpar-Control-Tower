"""Score de maturidade FinOps (0-100) por empresa, inspirado no modelo Crawl/Walk/Run da FinOps Foundation."""
from __future__ import annotations

from datetime import date

from ..db import q
from .common import add_months, loaded_costs, org_id, pct

WEIGHTS = [("tagging", "Tagging e alocação", 15), ("ownership", "Ownership", 10), ("showback", "Showback", 15),
           ("chargeback", "Chargeback", 10), ("standards", "Padronização", 10), ("optimization", "Otimização e compromissos", 15),
           ("waste", "Controle de desperdício", 15), ("forecast", "Previsibilidade (budget)", 10)]


def level(score: float) -> str:
    return "Run" if score >= 75 else "Walk" if score >= 45 else "Crawl"


def maturity(month: date) -> list[dict]:
    oid = org_id()
    rows = q("""SELECT company_code AS code, company_name AS name, SUM(cost_brl) AS c,
                       SUM(cost_brl) FILTER (WHERE fully_tagged) AS tagged,
                       SUM(cost_brl) FILTER (WHERE owner IS NOT NULL) AS owner,
                       SUM(cost_brl) FILTER (WHERE product_id IS NOT NULL AND application_id IS NOT NULL) AS showback,
                       SUM(cost_brl) FILTER (WHERE product_id IS NOT NULL AND chargeback_enabled) AS chargeback,
                       SUM(cost_brl) FILTER (WHERE std_ok) AS std,
                       SUM(cost_brl) FILTER (WHERE is_idle OR is_orphan) AS waste
                FROM v_cost WHERE org_id=:o AND month=:m GROUP BY 1,2""", o=oid, m=month)
    commit = {r["code"]: r for r in q("""SELECT co.code, SUM(c.coverage_pct*c.monthly_commit_brl)/NULLIF(SUM(c.monthly_commit_brl),0) AS cov,
                                                SUM(c.utilization_pct*c.monthly_commit_brl)/NULLIF(SUM(c.monthly_commit_brl),0) AS util
                                         FROM commitment c JOIN dim_company co ON co.id=c.company_id WHERE co.org_id=:o GROUP BY 1""", o=oid)}
    months = [add_months(month, -i) for i in range(3)]
    lc = loaded_costs(months)
    bud = q("""SELECT co.code, b.month, b.amount_brl AS a FROM budget b JOIN dim_company co ON co.id=b.company_id
               WHERE co.org_id=:o AND b.month = ANY(:m)""", o=oid, m=months)
    out = []
    for r in rows:
        c = r["c"] or 1
        cm = commit.get(r["code"], {"cov": 0, "util": 0})
        var = [abs(lc[(r["code"], b["month"])]["total"] / b["a"] - 1) * 100 for b in bud if b["code"] == r["code"] and (r["code"], b["month"]) in lc]
        avg_var = sum(var) / len(var) if var else 0
        raw = {
            "tagging": pct(r["tagged"] or 0, c), "ownership": pct(r["owner"] or 0, c), "showback": pct(r["showback"] or 0, c),
            "chargeback": pct(r["chargeback"] or 0, c), "standards": pct(r["std"] or 0, c),
            "optimization": min(100.0, (cm["cov"] or 0) / 85 * 100) * 0.6 + (cm["util"] or 0) * 0.4,
            "waste": max(0.0, 100 - pct(r["waste"] or 0, c) * 8), "forecast": max(0.0, 100 - avg_var * 5),
        }
        dims = [{"key": k, "name": n, "weight": w, "score": round(raw[k], 1)} for k, n, w in WEIGHTS]
        score = sum(d["score"] * d["weight"] for d in dims) / sum(w for _, _, w in WEIGHTS)
        out.append({"code": r["code"], "name": r["name"], "score": round(score, 1), "level": level(score), "dimensions": dims})
    return sorted(out, key=lambda x: -x["score"])


def group_maturity(month: date, per_company: list[dict]) -> dict:
    weights = {r["code"]: r["c"] for r in q("SELECT company_code AS code, SUM(cost_brl) AS c FROM v_cost WHERE org_id=:o AND month=:m GROUP BY 1",
                                           o=org_id(), m=month)}
    tot = sum(weights.values()) or 1
    dims = []
    for k, n, w in WEIGHTS:
        dims.append({"key": k, "name": n, "weight": w,
                     "score": round(sum(next(d["score"] for d in c["dimensions"] if d["key"] == k) * weights.get(c["code"], 0) for c in per_company) / tot, 1)})
    score = sum(d["score"] * d["weight"] for d in dims) / sum(w for _, _, w in WEIGHTS)
    return {"code": "grupo", "name": "Grupo Simpar", "score": round(score, 1), "level": level(score), "dimensions": dims}
