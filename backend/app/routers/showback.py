import csv
import io
import json
from datetime import date

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..db import execute, q, q1
from ..services import kpis as K
from ..services.common import allocate, loaded_costs, org_id, parse_month, pct

router = APIRouter(prefix="/api/showback", tags=["showback-chargeback"])
NA_PRODUCT, NA_APP = "Sem produto (não alocado)", "Sem aplicação (não alocada)"


def _direct_by_company(m: date) -> dict[str, float]:
    return {r["company_code"]: r["c"] for r in q(
        "SELECT company_code, SUM(cost_brl) AS c FROM v_cost WHERE org_id=:o AND month=:m GROUP BY 1", o=org_id(), m=m)}


def _statement_rows(m: date, company: str | None = None) -> list[dict]:
    lc = loaded_costs([m])
    rows = q("""SELECT company_code, company_name, COALESCE(product_name, :na) AS product, product_id,
                       COALESCE(chargeback_enabled,false) AS chargeback_enabled, SUM(cost_brl) AS direct
                FROM v_cost WHERE org_id=:o AND month=:m GROUP BY 1,2,3,4,5 ORDER BY 1, direct DESC""",
             o=org_id(), m=m, na=NA_PRODUCT)
    by_co: dict[str, float] = {}
    for r in rows:
        by_co[r["company_code"]] = by_co.get(r["company_code"], 0) + r["direct"]
    out = []
    for r in rows:
        if company and r["company_code"] != company:
            continue
        shared = lc[(r["company_code"], m)]["shared"] * r["direct"] / by_co[r["company_code"]]
        total = r["direct"] + shared
        status = ("Não alocado — regularizar tags" if r["product_id"] is None else
                  "Faturável (chargeback)" if r["chargeback_enabled"] else "Somente showback")
        out.append({**r, "direct": round(r["direct"], 2), "shared": round(shared, 2), "total": round(total, 2),
                    "billable": round(total, 2) if (r["product_id"] and r["chargeback_enabled"]) else 0.0, "status": status})
    return out


@router.get("/summary")
def summary(month: str | None = None, company: str | None = None):
    m = parse_month(month)
    lines = q("""SELECT company_code, company_name, chargeback_enabled, COALESCE(product_name, :np) AS product,
                        COALESCE(application_name, :na) AS application, service, SUM(cost_brl) AS c, COUNT(*) AS n
                 FROM v_cost WHERE org_id=:o AND month=:m""" + (" AND company_code=:co" if company else "") +
             " GROUP BY 1,2,3,4,5,6", o=org_id(), m=m, np=NA_PRODUCT, na=NA_APP, co=company)
    tree: dict = {}
    for r in lines:
        c = tree.setdefault(r["company_code"], {"name": r["company_name"], "code": r["company_code"], "value": 0, "children": {}})
        p = c["children"].setdefault(r["product"], {"name": r["product"], "value": 0, "chargeback": r["chargeback_enabled"], "children": {}})
        a = p["children"].setdefault(r["application"], {"name": r["application"], "value": 0, "children": {}})
        s = a["children"].setdefault(r["service"], {"name": r["service"], "value": 0, "resources": 0})
        for node in (c, p, a, s):
            node["value"] += r["c"]
        s["resources"] += r["n"]

    def finish(n):
        if "children" in n:
            n["children"] = sorted((finish(x) for x in n["children"].values()), key=lambda x: -x["value"])
        n["value"] = round(n["value"], 2)
        return n

    nodes = sorted((finish(c) for c in tree.values()), key=lambda x: -x["value"])
    stm = _statement_rows(m, company)
    k = K.kpi_block(m, company)
    return {"month": m.isoformat(), "tree": nodes, "kpis": k,
            "totals": {"direct": round(sum(s["direct"] for s in stm), 2), "shared": round(sum(s["shared"] for s in stm), 2),
                       "billable": round(sum(s["billable"] for s in stm), 2),
                       "unallocated": round(sum(s["direct"] for s in stm if s["product"] == NA_PRODUCT), 2)},
            "by_company": [c for c in K.company_table(m) if not company or c["code"] == company]}


@router.get("/resources")
def resources(month: str | None = None, company: str | None = None, product: str | None = None,
              application: str | None = None, service: str | None = None, limit: int = 200):
    m = parse_month(month)
    where, p = ["org_id=:o", "month=:m"], dict(o=org_id(), m=m, lim=limit)
    if company:
        where.append("company_code=:co"); p["co"] = company
    if product:
        where.append("COALESCE(product_name,:np)=:pr"); p.update(pr=product, np=NA_PRODUCT)
    if application:
        where.append("COALESCE(application_name,:na)=:ap"); p.update(ap=application, na=NA_APP)
    if service:
        where.append("service=:sv"); p["sv"] = service
    return q(f"""SELECT resource_id, resource_name, cloud_code, service, region, env_norm AS environment, owner, cost_brl, tags
                 FROM v_cost WHERE {' AND '.join(where)} ORDER BY cost_brl DESC LIMIT :lim""", **p)


def _pools(m: date, override: dict | None = None) -> list[dict]:
    direct = _direct_by_company(m)
    comps = {r["code"]: r["name"] for r in q("SELECT code, name FROM dim_company WHERE org_id=:o ORDER BY id", o=org_id())}
    rows = q("""SELECT sp.id, sp.code, sp.name, sp.description, COALESCE(sc.cost_brl,0) AS cost,
                       COALESCE(ar.method,'proportional') AS method, COALESCE(ar.weights,'{}'::jsonb) AS weights
                FROM shared_pool sp JOIN dim_company co ON co.id=sp.company_id
                LEFT JOIN shared_cost_monthly sc ON sc.pool_id=sp.id AND sc.month=:m
                LEFT JOIN allocation_rule ar ON ar.pool_id=sp.id WHERE co.org_id=:o ORDER BY sp.id""", o=org_id(), m=m)
    out = []
    for r in rows:
        method, weights = r["method"], r["weights"]
        if override and override.get("pool_id") == r["id"]:
            method, weights = override["method"], override.get("weights", {})
        alloc = allocate(method, weights, {c: direct.get(c, 0.0) for c in comps}, r["cost"])
        out.append({**r, "method": method, "weights": weights, "cost": round(r["cost"], 2),
                    "allocation": [{"code": c, "name": comps[c], "amount": round(v, 2), "share": pct(v, r["cost"])}
                                   for c, v in alloc.items()]})
    return out


@router.get("/pools")
def pools(month: str | None = None):
    m = parse_month(month)
    pl = _pools(m)
    return {"month": m.isoformat(), "pools": pl, "total_shared": round(sum(p["cost"] for p in pl), 2)}


class RuleBody(BaseModel):
    method: str = Field(pattern="^(proportional|even|fixed)$")
    weights: dict[str, float] = {}


@router.post("/pools/{pool_id}/preview")
def preview(pool_id: int, body: RuleBody, month: str | None = None):
    m = parse_month(month)
    pl = _pools(m, {"pool_id": pool_id, **body.model_dump()})
    return next((p for p in pl if p["id"] == pool_id), {})


@router.put("/pools/{pool_id}/rule")
def set_rule(pool_id: int, body: RuleBody):
    if body.method == "fixed" and sum(body.weights.values()) <= 0:
        raise HTTPException(422, "Pesos devem somar mais que zero")
    if not q1("SELECT 1 AS x FROM shared_pool sp JOIN dim_company co ON co.id=sp.company_id WHERE sp.id=:i AND co.org_id=:o", i=pool_id, o=org_id()):
        raise HTTPException(404, "Pool não encontrado")
    execute("""INSERT INTO allocation_rule (pool_id, method, weights, updated_at) VALUES (:i,:m,CAST(:w AS jsonb), now())
               ON CONFLICT (pool_id) DO UPDATE SET method=EXCLUDED.method, weights=EXCLUDED.weights, updated_at=now()""",
            i=pool_id, m=body.method, w=json.dumps(body.weights))
    return {"ok": True}


@router.get("/statements")
def statements(month: str | None = None, company: str | None = None):
    m = parse_month(month)
    rows = _statement_rows(m, company)
    return {"month": m.isoformat(), "rows": rows,
            "totals": {"direct": round(sum(r["direct"] for r in rows), 2), "shared": round(sum(r["shared"] for r in rows), 2),
                       "total": round(sum(r["total"] for r in rows), 2), "billable": round(sum(r["billable"] for r in rows), 2)}}


@router.get("/statements.csv")
def statements_csv(month: str | None = None, company: str | None = None):
    m = parse_month(month)
    rows = _statement_rows(m, company)
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=";")
    w.writerow(["mes", "empresa", "produto", "custo_direto_brl", "rateio_compartilhado_brl", "total_brl", "valor_chargeback_brl", "status"])
    for r in rows:
        w.writerow([m.isoformat()[:7], r["company_name"], r["product"], r["direct"], r["shared"], r["total"], r["billable"], r["status"]])
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename=chargeback_{m.isoformat()[:7]}.csv"})
