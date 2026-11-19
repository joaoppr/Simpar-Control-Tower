from fastapi import APIRouter, HTTPException
from ..db import q, q1
from ..services import kpis as K
from ..services.common import add_months, org_id, parse_month, pct_change

router = APIRouter(prefix="/api/company", tags=["cio-empresa"])


@router.get("/{code}/overview")
def overview(code: str, month: str | None = None):
    co = q1("SELECT code, name, segment, color FROM dim_company WHERE org_id=:o AND code=:c", o=org_id(), c=code)
    if not co:
        raise HTTPException(404, "Empresa não encontrada")
    m = parse_month(month)
    dims = {d: K.breakdown(d, m, code) for d in ("cloud", "product", "application", "cost_center", "environment", "owner", "service")}
    # desvios: aplicacao x cloud com maior variacao absoluta vs. mes anterior
    prev = add_months(m, -1)
    dev = q("""SELECT COALESCE(application_name,'Sem aplicação') AS application, cloud_code,
                      COALESCE(SUM(cost_brl) FILTER (WHERE month=:m),0) AS cost,
                      COALESCE(SUM(cost_brl) FILTER (WHERE month=:p),0) AS prev
               FROM v_cost WHERE org_id=:o AND company_code=:c AND month IN (:m,:p)
               GROUP BY 1,2 HAVING COALESCE(SUM(cost_brl) FILTER (WHERE month=:m),0) + COALESCE(SUM(cost_brl) FILTER (WHERE month=:p),0) > 0""",
            o=org_id(), c=code, m=m, p=prev)
    deviations = []
    for d in dev:
        delta = d["cost"] - d["prev"]
        pc = pct_change(d["cost"], d["prev"])
        if abs(delta) >= 1500 and (pc is None or abs(pc) >= 5):
            deviations.append({**d, "delta": round(delta, 2), "pct": pc, "cost": round(d["cost"], 2), "prev": round(d["prev"], 2),
                               "severity": "alta" if abs(delta) >= 15000 else "média"})
    deviations.sort(key=lambda x: -abs(x["delta"]))
    opps = q("""SELECT id, title, opp_type, cloud_code, savings_monthly_brl, savings_pct, effort, term_days, risk, status, priority_score
                FROM v_opportunity WHERE org_id=:o AND company_code=:c AND status <> 'Capturada'
                ORDER BY savings_monthly_brl DESC LIMIT 8""", o=org_id(), c=code)
    quick = q("""SELECT id, title, opp_type, cloud_code, savings_monthly_brl, savings_pct, effort, term_days, risk, status
                 FROM v_opportunity WHERE org_id=:o AND company_code=:c AND status <> 'Capturada' AND effort='Baixo' AND term_days <= 20
                 ORDER BY savings_monthly_brl DESC LIMIT 6""", o=org_id(), c=code)
    by_type = q("""SELECT opp_type, SUM(savings_monthly_brl) AS savings, COUNT(*) AS n FROM v_opportunity
                   WHERE org_id=:o AND company_code=:c AND status <> 'Capturada' GROUP BY 1 ORDER BY 2 DESC""", o=org_id(), c=code)
    return {"company": co, "month": m.isoformat(), "kpis": K.kpi_block(m, code), "trend": K.trend(code), "breakdown": dims,
            "by_cloud_share": dims["cloud"], "deviations": deviations[:8], "opportunities": opps, "quick_wins": quick,
            "opportunities_by_type": by_type, "savings": K.savings_series(code)}
