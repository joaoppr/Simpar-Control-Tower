"""KPIs, series e quebras compartilhados por Executivo, CIO Empresa, Governanca e Copilot."""
from __future__ import annotations

from datetime import date

from ..db import q, q1
from .common import add_months, forecast, loaded_costs, month_range, org_id, pct, pct_change, reference_month

DIMENSIONS = {
    "cloud": ("cloud_code", "cloud_code"),
    "product": ("COALESCE(product_name,'Sem produto (não alocado)')", "product_name"),
    "application": ("COALESCE(application_name,'Sem aplicação (não alocado)')", "application_name"),
    "cost_center": ("COALESCE(cost_center_code,'Sem centro de custo')", "cost_center_code"),
    "environment": ("COALESCE(env_norm,'sem-ambiente')", "env_norm"),
    "owner": ("COALESCE(owner,'Sem owner')", "owner"),
    "service": ("service", "service"),
    "account": ("account_name", "account_name"),
    "company": ("company_name", "company_name"),
}


def _cf(company: str | None, cloud: str | None = None) -> str:
    s = ""
    if company:
        s += " AND company_code = :co"
    if cloud:
        s += " AND cloud_code = :cl"
    return s


def kpi_block(month: date, company: str | None = None, cloud: str | None = None) -> dict:
    oid, prev = org_id(), add_months(month, -1)
    p = dict(o=oid, m=month, p=prev, co=company, cl=cloud)
    r = q1(f"""
        SELECT SUM(cost_brl) FILTER (WHERE month=:m AND fully_tagged) AS tagged,
               SUM(cost_brl) FILTER (WHERE month=:m AND product_id IS NOT NULL AND application_id IS NOT NULL) AS showback,
               SUM(cost_brl) FILTER (WHERE month=:m AND product_id IS NOT NULL AND chargeback_enabled) AS chargeback,
               SUM(cost_brl) FILTER (WHERE month=:m AND (is_idle OR is_orphan)) AS idle_cost,
               SUM(cost_brl) FILTER (WHERE month=:m AND is_optimized) AS opt_cost,
               SUM(cost_brl) FILTER (WHERE month=:m) AS direct,
               COUNT(*) FILTER (WHERE month=:m) AS res,
               COUNT(*) FILTER (WHERE month=:m AND (is_idle OR is_orphan)) AS idle_n,
               COUNT(*) FILTER (WHERE month=:m AND is_optimized) AS opt_n,
               COUNT(*) FILTER (WHERE month=:m AND NOT fully_tagged) AS untagged_n
        FROM v_cost WHERE org_id=:o AND month IN (:m,:p){_cf(company, cloud)}""", **p)
    direct = r["direct"] or 0.0
    months = month_range()
    lc = loaded_costs([m for m in months if m <= month], company)
    cur_total = sum(v["total"] for (c, m), v in lc.items() if m == month and (not cloud))
    prev_total = sum(v["total"] for (c, m), v in lc.items() if m == prev and (not cloud))
    shared_alloc = sum(v["shared"] for (c, m), v in lc.items() if m == month)
    if cloud:   # filtro por cloud: custo direto da cloud (rateio compartilhado nao e por cloud)
        cur_total = direct
        prev_total = q1(f"SELECT SUM(cost_brl) AS c FROM v_cost WHERE org_id=:o AND month=:p{_cf(company, cloud)}", **p)["c"] or 0
        shared_alloc = 0.0
    year_months = [m for m in months if m.year == month.year and m <= month]
    ytd = sum(v["total"] for (c, m), v in lc.items() if m in year_months)
    bud = q1("""SELECT SUM(b.amount_brl) AS a FROM budget b JOIN dim_company co ON co.id=b.company_id
                WHERE co.org_id=:o AND b.month=:m""" + (" AND co.code=:co" if company else ""), o=oid, m=month, co=company)["a"] or 0
    sav = q1("""SELECT SUM(amount_brl) FILTER (WHERE month=:m) AS mo,
                       SUM(amount_brl) FILTER (WHERE date_part('year', month)=date_part('year', CAST(:m AS date)) AND month<=:m) AS ytd
                FROM savings_captured sc JOIN dim_company co ON co.id=sc.company_id
                WHERE co.org_id=:o""" + (" AND co.code=:co" if company else "") + (" AND sc.cloud_code=:cl" if cloud else ""),
             o=oid, m=month, co=company, cl=cloud)
    pot = q1("""SELECT SUM(savings_monthly_brl) AS s, COUNT(*) AS n FROM v_opportunity
                WHERE org_id=:o AND status <> 'Capturada'""" + (" AND company_code=:co" if company else "") + (" AND cloud_code=:cl" if cloud else ""),
             o=oid, co=company, cl=cloud)
    series = [sum(v["total"] for (c, m), v in lc.items() if m == mm) for mm in months if mm <= month]
    fc = forecast(series, 3)[0]["value"] if len(series) >= 3 else None
    return {
        "total_spend": round(cur_total, 2), "direct_spend": round(direct, 2), "shared_allocated": round(shared_alloc, 2),
        "prev_spend": round(prev_total, 2), "mom_pct": pct_change(cur_total, prev_total), "ytd_spend": round(ytd, 2),
        "budget": round(bud, 2), "budget_var_pct": pct_change(cur_total, bud) if bud and not cloud else None,
        "saving_captured_month": round(sav["mo"] or 0, 2), "saving_captured_ytd": round(sav["ytd"] or 0, 2),
        "saving_potential": round(pot["s"] or 0, 2), "opportunities_open": pot["n"],
        "saving_potential_pct": pct(pot["s"] or 0, cur_total),
        "tag_coverage": pct(r["tagged"] or 0, direct), "showback_coverage": pct(r["showback"] or 0, direct),
        "chargeback_coverage": pct(r["chargeback"] or 0, direct),
        "idle_pct": pct(r["idle_cost"] or 0, direct), "idle_cost": round(r["idle_cost"] or 0, 2),
        "idle_resources_pct": pct(r["idle_n"] or 0, r["res"] or 0), "idle_resources": r["idle_n"],
        "optimized_pct": pct(r["opt_cost"] or 0, direct), "optimized_resources_pct": pct(r["opt_n"] or 0, r["res"] or 0),
        "resources": r["res"], "untagged_resources": r["untagged_n"], "forecast_next_month": fc,
    }


def trend(company: str | None = None) -> list[dict]:
    """12 meses realizados (com rateio) + budget + 3 meses de forecast."""
    months = month_range()
    lc = loaded_costs(months, company)
    actual = [round(sum(v["total"] for (c, m), v in lc.items() if m == mm), 2) for mm in months]
    allm = months + [add_months(months[-1], i) for i in (1, 2, 3)]
    bud = {r["month"]: r["a"] for r in q("""SELECT b.month, SUM(b.amount_brl) AS a FROM budget b JOIN dim_company co ON co.id=b.company_id
                  WHERE co.org_id=:o""" + (" AND co.code=:co" if company else "") + " GROUP BY 1", o=org_id(), co=company)}
    fc = forecast(actual, 3)
    out = []
    for i, m in enumerate(allm):
        row = {"month": m.isoformat(), "actual": actual[i] if i < 12 else None, "budget": bud.get(m)}
        if i == 11:
            row.update(forecast=actual[i], forecast_low=actual[i], forecast_high=actual[i])
        if i >= 12:
            f = fc[i - 12]
            row.update(forecast=f["value"], forecast_low=f["low"], forecast_high=f["high"])
        out.append(row)
    return out


def breakdown(dim: str, month: date, company: str | None = None, cloud: str | None = None, limit: int | None = None) -> list[dict]:
    expr, _ = DIMENSIONS[dim]
    prev = add_months(month, -1)
    rows = q(f"""
        SELECT {expr} AS name,
               COALESCE(SUM(cost_brl) FILTER (WHERE month=:m),0) AS cost,
               COALESCE(SUM(cost_brl) FILTER (WHERE month=:p),0) AS prev
        FROM v_cost WHERE org_id=:o AND month IN (:m,:p){_cf(company, cloud)}
        GROUP BY 1 HAVING SUM(cost_brl) FILTER (WHERE month=:m) > 0 ORDER BY cost DESC""",
             o=org_id(), m=month, p=prev, co=company, cl=cloud)
    tot = sum(r["cost"] for r in rows) or 1.0
    out = [{"name": r["name"], "cost": round(r["cost"], 2), "prev": round(r["prev"], 2),
            "share": round(100 * r["cost"] / tot, 2), "mom_pct": pct_change(r["cost"], r["prev"])} for r in rows]
    return out[:limit] if limit else out


def top_consumers(month: date, dimension: str = "application", limit: int = 20, company: str | None = None) -> list[dict]:
    prev = add_months(month, -1)
    if dimension == "resource":
        sel, grp = "resource_name AS name, company_name, cloud_code, service AS detail, resource_id AS key", "resource_name, company_name, cloud_code, service, resource_id"
    elif dimension == "account":
        sel, grp = "account_name AS name, company_name, cloud_code, '' AS detail, account_id AS key", "account_name, company_name, cloud_code, account_id"
    else:
        sel = ("COALESCE(application_name,'Sem aplicação') AS name, company_name, string_agg(DISTINCT cloud_code, ' · ') AS cloud_code, "
               "COALESCE(product_name,'Sem produto') AS detail, COALESCE(application_id,0) AS key")
        grp = "application_name, company_name, product_name, application_id"
    rows = q(f"""SELECT {sel},
                        COALESCE(SUM(cost_brl) FILTER (WHERE month=:m),0) AS cost,
                        COALESCE(SUM(cost_brl) FILTER (WHERE month=:p),0) AS prev
                 FROM v_cost WHERE org_id=:o AND month IN (:m,:p){_cf(company)}
                 GROUP BY {grp} HAVING SUM(cost_brl) FILTER (WHERE month=:m) > 0
                 ORDER BY cost DESC LIMIT :lim""", o=org_id(), m=month, p=prev, co=company, lim=limit)
    total = q1("SELECT SUM(cost_brl) AS c FROM v_cost WHERE org_id=:o AND month=:m" + _cf(company), o=org_id(), m=month, co=company)["c"] or 1
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
        r["share"] = round(100 * r["cost"] / total, 2)
        r["mom_pct"] = pct_change(r["cost"], r["prev"])
        r["cost"] = round(r["cost"], 2)
    return rows


def company_table(month: date) -> list[dict]:
    """Empresa x custo (com rateio), budget, variacao e custo por cloud."""
    prev = add_months(month, -1)
    lc = loaded_costs([month, prev])
    bud = {r["code"]: r["a"] for r in q("""SELECT co.code, b.amount_brl AS a FROM budget b JOIN dim_company co ON co.id=b.company_id
                                           WHERE co.org_id=:o AND b.month=:m""", o=org_id(), m=month)}
    clouds = q("""SELECT company_code, cloud_code, SUM(cost_brl) AS c FROM v_cost WHERE org_id=:o AND month=:m GROUP BY 1,2""",
               o=org_id(), m=month)
    comps = q("SELECT code, name, color FROM dim_company WHERE org_id=:o ORDER BY id", o=org_id())
    total = sum(v["total"] for (c, m), v in lc.items() if m == month) or 1.0
    out = []
    for co in comps:
        cur = lc.get((co["code"], month), {"direct": 0, "shared": 0, "total": 0})
        pv = lc.get((co["code"], prev), {"total": 0})
        b = bud.get(co["code"], 0)
        out.append({**co, "cost": round(cur["total"], 2), "direct": round(cur["direct"], 2), "shared": round(cur["shared"], 2),
                    "budget": round(b, 2), "variance_pct": pct_change(cur["total"], b), "mom_pct": pct_change(cur["total"], pv["total"]),
                    "share": round(100 * cur["total"] / total, 2),
                    "by_cloud": {c["cloud_code"]: round(c["c"], 2) for c in clouds if c["company_code"] == co["code"]}})
    return out


def cloud_table(month: date) -> list[dict]:
    prev = add_months(month, -1)
    rows = q("""SELECT v.cloud_code AS code, dc.name, dc.color,
                       COALESCE(SUM(cost_brl) FILTER (WHERE month=:m),0) AS cost,
                       COALESCE(SUM(cost_brl) FILTER (WHERE month=:p),0) AS prev
                FROM v_cost v JOIN dim_cloud dc ON dc.code=v.cloud_code
                WHERE org_id=:o AND month IN (:m,:p) GROUP BY 1,2,3 ORDER BY cost DESC""", o=org_id(), m=month, p=prev)
    shared = q1("SELECT SUM(cost_brl) AS c FROM v_shared_cost WHERE org_id=:o AND month=:m", o=org_id(), m=month)["c"] or 0
    sharedp = q1("SELECT SUM(cost_brl) AS c FROM v_shared_cost WHERE org_id=:o AND month=:m", o=org_id(), m=prev)["c"] or 0
    dtot, dptot = sum(r["cost"] for r in rows) or 1.0, sum(r["prev"] for r in rows) or 1.0
    for r in rows:      # custos compartilhados distribuidos proporcionalmente ao consumo direto de cada cloud
        r["cost"] = round(r["cost"] + shared * r["cost"] / dtot, 2)
        r["prev"] = r["prev"] + sharedp * r["prev"] / dptot
    tot = sum(r["cost"] for r in rows) or 1.0
    for r in rows:
        r["share"] = round(100 * r["cost"] / tot, 2)
        r["mom_pct"] = pct_change(r["cost"], r["prev"])
        del r["prev"]
    return rows


def savings_series(company: str | None = None) -> list[dict]:
    rows = q("""SELECT sc.month, SUM(sc.amount_brl) AS captured FROM savings_captured sc
                JOIN dim_company co ON co.id=sc.company_id WHERE co.org_id=:o""" + (" AND co.code=:co" if company else "") + " GROUP BY 1 ORDER BY 1",
             o=org_id(), co=company)
    got = {r["month"]: r["captured"] for r in rows}
    return [{"month": m.isoformat(), "captured": round(got.get(m, 0), 2)} for m in month_range()]
