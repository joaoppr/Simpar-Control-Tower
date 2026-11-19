import csv
import io

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from ..db import q, q1
from ..services.common import org_id, parse_month

router = APIRouter(prefix="/api/inventory", tags=["inventario"])

SORTS = {"cost": "cost_brl", "name": "resource_name", "company": "company_name", "cloud": "cloud_code", "service": "service",
         "region": "region", "owner": "owner", "product": "product_name", "application": "application_name", "environment": "env_norm"}


def _filters(month, company, cloud, account, service, region, environment, owner, product, application, search, tagged, idle, standard):
    w, p = ["org_id=:o", "month=:m"], {"o": org_id(), "m": parse_month(month)}
    for col, val, key in (("company_code", company, "co"), ("cloud_code", cloud, "cl"), ("account_name", account, "ac"),
                          ("service", service, "sv"), ("region", region, "rg"), ("env_norm", environment, "ev"),
                          ("product_name", product, "pr"), ("application_name", application, "ap")):
        if val:
            w.append(f"{col}=:{key}")
            p[key] = val
    if owner:
        if owner == "__none__":
            w.append("owner IS NULL")
        else:
            w.append("owner=:ow")
            p["ow"] = owner
    if search:
        w.append("(resource_name ILIKE :s OR application_name ILIKE :s OR owner ILIKE :s)")
        p["s"] = f"%{search}%"
    if tagged is not None:
        w.append("fully_tagged" if tagged else "NOT fully_tagged")
    if idle is not None:
        w.append("(is_idle OR is_orphan)" if idle else "NOT (is_idle OR is_orphan)")
    if standard is not None:
        w.append("std_ok" if standard else "NOT std_ok")
    return " AND ".join(w), p


@router.get("")
def inventory(month: str | None = None, company: str | None = None, cloud: str | None = None, account: str | None = None,
              service: str | None = None, region: str | None = None, environment: str | None = None, owner: str | None = None,
              product: str | None = None, application: str | None = None, q_: str | None = Query(None, alias="q"),
              tagged: bool | None = None, idle: bool | None = None, standard: bool | None = None,
              sort: str = "cost", dir: str = "desc", page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=500)):
    where, p = _filters(month, company, cloud, account, service, region, environment, owner, product, application, q_, tagged, idle, standard)
    agg = q1(f"SELECT COUNT(*) AS n, COALESCE(SUM(cost_brl),0) AS c FROM v_cost WHERE {where}", **p)
    col = SORTS.get(sort, "cost_brl")
    d = "ASC" if dir.lower() == "asc" else "DESC"
    rows = q(f"""SELECT resource_id, company_name, company_code, cloud_code, account_name, service, resource_type, resource_name,
                        region, owner, product_name, application_name, env_norm AS environment, cost_brl, fully_tagged, std_ok,
                        (is_idle OR is_orphan) AS idle, is_optimized, cpu_avg, arch, tags
                 FROM v_cost WHERE {where} ORDER BY {col} {d} NULLS LAST, resource_id LIMIT :lim OFFSET :off""",
             **p, lim=page_size, off=(page - 1) * page_size)
    return {"total": agg["n"], "total_cost": round(agg["c"], 2), "page": page, "page_size": page_size, "rows": rows}


@router.get("/facets")
def facets(month: str | None = None):
    m = parse_month(month)

    def f(expr):
        return q(f"""SELECT {expr} AS value, COUNT(*) AS n FROM v_cost WHERE org_id=:o AND month=:m
                     GROUP BY 1 ORDER BY n DESC""", o=org_id(), m=m)
    return {"company": f("company_code"), "cloud": f("cloud_code"), "service": f("service"), "region": f("region"),
            "environment": f("COALESCE(env_norm,'sem-ambiente')"), "product": f("COALESCE(product_name,'')"),
            "account": f("account_name"), "owner": f("COALESCE(owner,'')")}


@router.get("/export.csv")
def export_csv(month: str | None = None, company: str | None = None, cloud: str | None = None, service: str | None = None,
               tagged: bool | None = None):
    where, p = _filters(month, company, cloud, None, service, None, None, None, None, None, None, tagged, None, None)
    rows = q(f"""SELECT company_name, cloud_code, account_name, service, resource_name, region, owner, product_name,
                        application_name, env_norm, cost_brl FROM v_cost WHERE {where} ORDER BY cost_brl DESC LIMIT 50000""", **p)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["empresa", "cloud", "conta", "servico", "recurso", "regiao", "owner", "produto", "aplicacao", "ambiente", "custo_mensal_brl"])
    for r in rows:
        w.writerow(list(r.values()))
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=inventario_multicloud.csv"})
