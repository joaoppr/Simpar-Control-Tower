from fastapi import APIRouter, Query

from ..db import q, q1
from ..services import kpis as K
from ..services.common import org_id, parse_month, pct
from ..services.maturity import group_maturity, maturity

router = APIRouter(prefix="/api/governance", tags=["governanca"])

ISSUES = {
    "no_owner": ("Sem owner", "owner IS NULL"),
    "no_product": ("Sem produto", "product_id IS NULL"),
    "no_application": ("Sem aplicação", "application_id IS NULL"),
    "no_cost_center": ("Sem centro de custo", "cost_center_id IS NULL"),
    "no_environment": ("Sem ambiente", "environment IS NULL"),
    "non_standard": ("Fora de padrão", "NOT std_ok"),
}


@router.get("/summary")
def summary(month: str | None = None, company: str | None = None):
    m = parse_month(month)
    base, p = "org_id=:o AND month=:m" + (" AND company_code=:co" if company else ""), dict(o=org_id(), m=m, co=company)
    sel = ", ".join(f"COUNT(*) FILTER (WHERE {c}) AS n_{k}, COALESCE(SUM(cost_brl) FILTER (WHERE {c}),0) AS c_{k}" for k, (_, c) in ISSUES.items())
    t = q1(f"""SELECT COUNT(*) AS n, SUM(cost_brl) AS c, COUNT(*) FILTER (WHERE NOT fully_tagged) AS n_untagged,
                      COALESCE(SUM(cost_brl) FILTER (WHERE NOT fully_tagged),0) AS c_untagged,
                      COUNT(*) FILTER (WHERE fully_tagged) AS n_tagged, {sel}
               FROM v_cost WHERE {base}""", **p)
    issues = [{"key": k, "name": nm, "resources": t[f"n_{k}"], "cost": round(t[f"c_{k}"], 2),
               "pct_resources": pct(t[f"n_{k}"], t["n"]), "pct_cost": pct(t[f"c_{k}"], t["c"])} for k, (nm, _) in ISSUES.items()]
    by_company = q("""SELECT company_code AS code, company_name AS name, COUNT(*) AS resources, SUM(cost_brl) AS cost,
                             COUNT(*) FILTER (WHERE NOT fully_tagged) AS untagged,
                             SUM(cost_brl) FILTER (WHERE fully_tagged) AS tagged_cost,
                             COUNT(*) FILTER (WHERE owner IS NULL) AS no_owner, COUNT(*) FILTER (WHERE product_id IS NULL) AS no_product,
                             COUNT(*) FILTER (WHERE cost_center_id IS NULL) AS no_cost_center, COUNT(*) FILTER (WHERE NOT std_ok) AS non_standard
                      FROM v_cost WHERE org_id=:o AND month=:m GROUP BY 1,2 ORDER BY cost DESC""", o=org_id(), m=m)
    for r in by_company:
        r["tag_coverage"] = pct(r["tagged_cost"] or 0, r["cost"])
        r["tag_coverage_resources"] = pct(r["resources"] - r["untagged"], r["resources"])
    by_cloud = q("""SELECT cloud_code AS code, COUNT(*) AS resources, SUM(cost_brl) AS cost,
                           SUM(cost_brl) FILTER (WHERE fully_tagged) AS tagged_cost
                    FROM v_cost WHERE org_id=:o AND month=:m""" + (" AND company_code=:co" if company else "") + " GROUP BY 1 ORDER BY cost DESC",
                 o=org_id(), m=m, co=company)
    for r in by_cloud:
        r["tag_coverage"] = pct(r["tagged_cost"] or 0, r["cost"])
    mat = maturity(m)
    grp = group_maturity(m, mat)
    policy = q("SELECT tag_key, required, allowed_values, description FROM tag_policy WHERE org_id=:o ORDER BY id", o=org_id())
    return {"month": m.isoformat(), "kpis": K.kpi_block(m, company),
            "totals": {"resources": t["n"], "cost": round(t["c"] or 0, 2), "tag_coverage": pct(t["n"] - t["n_untagged"], t["n"]),
                       "tag_coverage_cost": pct((t["c"] or 0) - t["c_untagged"], t["c"] or 1),
                       "untagged_resources": t["n_untagged"], "untagged_cost": round(t["c_untagged"], 2)},
            "issues": issues, "by_company": by_company, "by_cloud": by_cloud, "maturity": mat, "maturity_group": grp,
            "policy": policy, "selected_maturity": next((x for x in mat if x["code"] == company), None) if company else grp}


@router.get("/violations")
def violations(month: str | None = None, company: str | None = None, cloud: str | None = None, issue: str = "any",
               page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200)):
    m = parse_month(month)
    w, p = ["org_id=:o", "month=:m"], dict(o=org_id(), m=m)
    if company:
        w.append("company_code=:co"); p["co"] = company
    if cloud:
        w.append("cloud_code=:cl"); p["cl"] = cloud
    if issue in ISSUES:
        w.append(ISSUES[issue][1])
    else:
        w.append("(" + " OR ".join(c for _, c in ISSUES.values()) + ")")
    arr = ", ".join(f"CASE WHEN {c} THEN '{k}' END" for k, (_, c) in ISSUES.items())
    where = " AND ".join(w)
    tot = q1(f"SELECT COUNT(*) AS n, COALESCE(SUM(cost_brl),0) AS c FROM v_cost WHERE {where}", **p)
    rows = q(f"""SELECT resource_id, company_name, cloud_code, account_name, service, resource_name, region, cost_brl,
                        array_remove(ARRAY[{arr}], NULL) AS issues, owner, product_name, application_name, environment
                 FROM v_cost WHERE {where} ORDER BY cost_brl DESC LIMIT :lim OFFSET :off""", **p, lim=page_size, off=(page - 1) * page_size)
    for r in rows:
        r["issue_labels"] = [ISSUES[i][0] for i in r["issues"]]
    return {"total": tot["n"], "total_cost": round(tot["c"], 2), "page": page, "page_size": page_size, "rows": rows}
