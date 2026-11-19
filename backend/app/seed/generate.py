"""Gerador deterministico da base de demonstracao (dados 100% ficticios)."""
from __future__ import annotations

import json
import math
import random
import uuid
from datetime import date, datetime, timedelta, timezone

from ..config import ROOT
from ..db import engine
from .catalog import (CATEGORIES, CLOUDS, COMMITMENT_KINDS, COMPANIES, COST_CENTERS, OPP_TYPES, PRODUCTS,
                      REGION_W, REGIONS, SERVICE_CAT, SERVICES, SHARED_POOLS, SHARED_SHARE_OF_TOTAL,
                      TOTAL_REF_MONTH)

DB_DIR = ROOT / "database"
TAG_KEYS = ["owner", "product", "application", "cost-center", "environment"]
ENV_VARIANTS = {"prod": ["Production", "producao", "PRD", "Prod"], "hml": ["homolog", "Staging", "HML"],
                "dev": ["development", "Dev", "desenvolvimento"]}
UNIT_PRICE = {"compute": 0.55, "db": 1.6, "k8s": 2.9, "block": 0.55, "object": 0.12, "logs": 0.9, "other": 1.0}
UNIT_NAME = {"compute": "horas", "db": "horas", "k8s": "horas-nó", "block": "GB-mês", "object": "GB-mês",
             "logs": "GB ingeridos", "other": "unidades"}
STATUS_W = [("Identificada", 52), ("Em análise", 15), ("Aprovada", 9), ("Em execução", 8), ("Capturada", 16)]
EFFORT_I = {"Baixo": 1, "Médio": 2, "Alto": 3}


def add_months(d: date, n: int) -> date:
    y = d.year + (d.month - 1 + n) // 12
    return date(y, (d.month - 1 + n) % 12 + 1, 1)


def default_ref() -> date:
    t = date.today()
    return add_months(date(t.year, t.month, 1), -1)   # ultimo mes fechado


def reset_schema() -> None:
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        cur.execute((DB_DIR / "schema.sql").read_text(encoding="utf-8"))
        cur.execute((DB_DIR / "views.sql").read_text(encoding="utf-8"))
        raw.commit()
    finally:
        raw.close()


def _weighted(rnd: random.Random, pairs):
    tot = sum(w for _, w in pairs)
    x = rnd.random() * tot
    for v, w in pairs:
        x -= w
        if x <= 0:
            return v
    return pairs[-1][0]


def seed_database(ref: date | None = None, seed: int = 42, verbose: bool = True) -> dict:
    ref = ref or default_ref()
    rnd = random.Random(seed)
    months = [add_months(ref, -11 + i) for i in range(12)]
    budget_months = [add_months(ref, -11 + i) for i in range(15)]
    log = print if verbose else (lambda *a, **k: None)

    reset_schema()
    raw = engine.raw_connection()
    cur = raw.cursor()

    def copy(table: str, cols: list[str], rows: list[tuple]):
        if not rows:
            return
        with cur.copy(f"COPY {table} ({','.join(cols)}) FROM STDIN") as cp:
            for r in rows:
                cp.write_row(r)

    # ---- org, clouds, companies
    cur.execute("INSERT INTO org (code, name) VALUES ('simpar','Grupo Simpar') RETURNING id")
    org_id = cur.fetchone()[0]
    copy("dim_cloud", ["code", "name", "color", "cost_source"], CLOUDS)
    comp = {}
    for i, c in enumerate(COMPANIES, start=1):
        comp[c[0]] = dict(id=i, code=c[0], name=c[1], seg=c[2], color=c[3], share=c[4], growth=c[5], bias=c[6],
                          cov=c[7], mix=c[8])
    copy("dim_company", ["id", "org_id", "code", "name", "segment", "color"],
         [(v["id"], org_id, v["code"], v["name"], v["seg"], v["color"]) for v in comp.values()])

    # ---- tag policy
    pol = [("owner", True, None, "Equipe responsavel pelo recurso"),
           ("product", True, None, "Produto de negocio atendido"),
           ("application", True, None, "Aplicacao proprietaria do recurso"),
           ("cost-center", True, None, "Centro de custo contabil"),
           ("environment", True, json.dumps(["prod", "hml", "dev"]), "Ambiente: prod, hml ou dev")]
    copy("tag_policy", ["org_id", "tag_key", "required", "allowed_values", "description"],
         [(org_id, k, r, a, d) for k, r, a, d in pol])

    # ---- accounts
    accounts, acc_rows, acc_id = {}, [], 0
    for c in comp.values():
        for cloud in c["mix"]:
            lst = []
            for scope in ["prod", "hml", "dev"] + (["shared"] if rnd.random() < 0.3 else []):
                acc_id += 1
                if cloud == "aws":
                    ext = "".join(rnd.choice("0123456789") for _ in range(12))
                elif cloud == "azure":
                    ext = str(uuid.UUID(int=rnd.getrandbits(128)))
                elif cloud == "oci":
                    ext = "ocid1.compartment.oc1..aaaa" + "".join(rnd.choice("abcdefghijklmnopqrstuvwxyz234567") for _ in range(20))
                elif cloud == "gcp":
                    ext = f"{c['code']}-{scope}-{rnd.randint(100000, 999999)}"
                else:
                    ext = "".join(rnd.choice("0123456789abcdef") for _ in range(32))
                acc_rows.append((acc_id, c["id"], cloud, ext, f"{c['code']}-{cloud}-{scope}", scope, "active"))
                lst.append((acc_id, scope))
            accounts[(c["code"], cloud)] = lst
    copy("cloud_account", ["id", "company_id", "cloud_code", "external_id", "name", "env_scope", "status"], acc_rows)

    # ---- products, applications, cost centers
    prod_rows, app_rows, cc_rows = [], [], []
    apps = {}          # company -> list of dict(app_id, product_id, weight, cc_id, owner, code)
    pid = aid = ccid = 0
    for c in comp.values():
        ccs = []
        for code, nm in COST_CENTERS[: 4 + rnd.randint(0, 2)]:
            ccid += 1
            cc_rows.append((ccid, c["id"], f"{c['code'].upper()}-{code}", nm))
            ccs.append(ccid)
        apps[c["code"]] = []
        for k, (pcode, pname, powner, cb, alist) in enumerate(PRODUCTS[c["code"]]):
            pid += 1
            prod_rows.append((pid, c["id"], pcode, pname, powner, cb))
            for acode, aname, crit, w in alist:
                aid += 1
                app_rows.append((aid, c["id"], pid, acode, aname, crit))
                apps[c["code"]].append(dict(app_id=aid, product_id=pid, weight=w, cc_id=ccs[k % len(ccs)],
                                            owner=powner, code=acode, ccs=ccs))
    copy("dim_product", ["id", "company_id", "code", "name", "owner", "chargeback_enabled"], prod_rows)
    copy("dim_application", ["id", "company_id", "product_id", "code", "name", "criticality"], app_rows)
    copy("dim_cost_center", ["id", "company_id", "code", "name"], cc_rows)

    # ---- resources (pass 1: atributos e custo base)
    direct_total = TOTAL_REF_MONTH * (1 - SHARED_SHARE_OF_TOTAL)
    res = []
    rid = 0
    for c in comp.values():
        for cloud, cshare in c["mix"].items():
            ctarget = direct_total * c["share"] * cshare
            svcs = list(SERVICES[cloud])
            if cloud == "oci" and c["code"] != "simpar":
                svcs = [(n, w * (0.55 if n == "Exadata Database Service" else 1), t, ty) for n, w, t, ty in svcs]
            wsum = sum(s[1] for s in svcs)
            for svc, w, typical, rtype in svcs:
                target = ctarget * w / wsum
                n = max(1, min(700, round(target / typical)))
                if svc == "Exadata Database Service":
                    n = max(1, min(n, 6))
                sigma = 0.35 if svc == "Exadata Database Service" else 1.0
                raw_w = [rnd.lognormvariate(0, sigma) for _ in range(n)]
                sw = sum(raw_w)
                cat = SERVICE_CAT.get(svc, "other")
                for j in range(n):
                    rid += 1
                    env = _weighted(rnd, [("prod", 0.58), ("hml", 0.19), ("dev", 0.23)])
                    emult = {"prod": 1.0, "hml": 0.55, "dev": 0.4}[env]
                    scope_accs = [a for a, s in accounts[(c["code"], cloud)] if s == env] or [accounts[(c["code"], cloud)][0][0]]
                    app = rnd.choices(apps[c["code"]], weights=[a["weight"] for a in apps[c["code"]]])[0]
                    cc_id = app["cc_id"] if rnd.random() > 0.15 else rnd.choice(app["ccs"])
                    complete = rnd.random() < c["cov"]
                    missing = set()
                    if not complete:
                        k = _weighted(rnd, [(1, 45), (2, 30), (3, 15), (4, 10)])
                        keys = list(TAG_KEYS)
                        wts = [25, 20, 25, 20, 10]
                        while len(missing) < k:
                            missing.add(rnd.choices(keys, weights=wts)[0])
                        if "product" in missing and rnd.random() < 0.7:
                            missing.add("application")
                    env_tag = env
                    if "environment" not in missing and rnd.random() < 0.08:
                        env_tag = rnd.choice(ENV_VARIANTS[env])
                    owner = None if "owner" in missing else app["owner"]
                    product_id = None if "product" in missing else app["product_id"]
                    application_id = None if "application" in missing else app["app_id"]
                    cost_center_id = None if "cost-center" in missing else cc_id
                    environment = None if "environment" in missing else env_tag
                    tags = {}
                    if owner:
                        tags["owner"] = owner
                    if product_id:
                        tags["product"] = next(p[2] for p in prod_rows if p[0] == product_id)
                    if application_id:
                        tags["application"] = app["code"]
                    if cost_center_id:
                        tags["cost-center"] = next(x[2] for x in cc_rows if x[0] == cost_center_id)
                    if environment:
                        tags["environment"] = environment
                    naming_ok = rnd.random() < (0.93 if complete else 0.66)
                    slug = svc.lower().replace(" ", "-").replace("/", "-")
                    name = (f"{c['code']}-{app['code']}-{env}-{slug}-{j + 1:03d}" if naming_ok
                            else rnd.choice(["srv-teste", "vm-novo", "tmp-recurso", "Servidor_", "test-"]) + str(rnd.randint(1, 999)))
                    cpu = None
                    state = "running"
                    is_idle = is_orphan = False
                    if cat in ("compute", "db", "k8s"):
                        u = rnd.random()
                        cpu = (rnd.uniform(0.5, 4) if u < 0.10 else rnd.uniform(5, 25) if u < 0.36 else
                               rnd.uniform(25, 65) if u < 0.86 else rnd.uniform(65, 90))
                        is_idle = cpu < 4 and svc != "Exadata Database Service"
                    elif cat == "block" and rnd.random() < 0.11:
                        state, is_orphan = "unattached", True
                    arch = ("arm" if rnd.random() < 0.12 else "x86") if cat in ("compute", "db") else None
                    created = date.today() - timedelta(days=rnd.randint(40, 1100))
                    u = rnd.random()
                    start_k, end_k = 0, 11
                    if u < 0.12:
                        start_k = rnd.randint(1, 10)
                        created = months[start_k]
                    elif u < 0.17:
                        end_k = rnd.randint(2, 9)
                    region = rnd.choices(REGIONS[cloud], weights=REGION_W[: len(REGIONS[cloud])])[0]
                    base = target * raw_w[j] / sw * emult
                    res.append(dict(
                        id=rid, account_id=rnd.choice(scope_accs), company=c["code"],
                        company_id=c["id"], cloud=cloud, service=svc, rtype=rtype, name=name, region=region,
                        env=env, environment=environment, owner=owner, product_id=product_id,
                        application_id=application_id, cost_center_id=cost_center_id, tags=tags, state=state,
                        cpu=cpu, arch=arch, is_idle=is_idle, is_orphan=is_orphan, is_optimized=False,
                        naming_ok=naming_ok, created=created, retired=(months[end_k] + timedelta(days=27)) if end_k < 11 else None,
                        base=base, start_k=start_k, end_k=end_k, cat=cat,
                        noise=[rnd.lognormvariate(0, 0.035) for _ in range(12)], captured_k=None, cap_pct=0.0,
                        cap_zero=False))
    if verbose:
        log(f"recursos gerados: {len(res)}")

    # ---- escala por empresa para bater o alvo do mes de referencia
    def g(c, k):
        return (1 + c["growth"]) ** (k - 11) * (1 + 0.015 * math.sin(2 * math.pi * k / 12))

    def cost_at(r, c, k):
        if k < r["start_k"] or k > r["end_k"]:
            return 0.0
        ramp = 0.55 if k == r["start_k"] and r["start_k"] > 0 else 1.0
        return r["base"] * g(c, k) * r["noise"][k] * ramp

    for c in comp.values():
        rs = [r for r in res if r["company"] == c["code"]]
        tot = sum(cost_at(r, c, 11) for r in rs)
        f = direct_total * c["share"] / tot
        for r in rs:
            r["base"] *= f

    # ---- oportunidades por recurso (exclusivas: sem dupla contagem)
    opp_def = {t[0]: t for t in OPP_TYPES}
    opps = []

    def mk_opp(r, typ, pct, cost_ref, title, desc, status=None):
        _, _, effort, term, risk, _ = opp_def[typ]
        if typ in ("rightsizing", "off_hours") and r["env"] != "prod":
            risk = "Baixo"
        if typ == "rightsizing" and rnd.random() < 0.25:
            effort = "Baixo"
        term = max(5, int(term * rnd.uniform(0.8, 1.3)))
        st = status or _weighted(rnd, STATUS_W)
        opps.append(dict(company=r["company"], company_id=r["company_id"], cloud=r["cloud"], account_id=r["account_id"],
                         resource=r, rid=r["id"], typ=typ, title=title, desc=desc, cost=cost_ref,
                         sav=cost_ref * pct, pct=pct * 100, effort=effort, term=term, risk=risk, status=st,
                         owner=r["owner"], captured_k=None))
        return opps[-1]

    for r in res:
        if r["end_k"] < 11:
            continue
        c = comp[r["company"]]
        cost_ref = cost_at(r, c, 11)
        if cost_ref <= 0:
            continue
        cat, svc, env = r["cat"], r["service"], r["env"]
        o = None
        if r["is_idle"]:
            o = mk_opp(r, "idle_resources", rnd.uniform(0.9, 1.0), cost_ref, f"Desligar {r['name']} (sem uso)",
                       f"CPU média de {r['cpu']:.1f}% nos últimos 30 dias em {svc}; sem tráfego relevante.")
        elif r["is_orphan"]:
            o = mk_opp(r, "orphan_resources", 1.0, cost_ref, f"Remover volume órfão {r['name']}",
                       f"Volume não anexado a nenhuma instância em {svc}; validar snapshot antes de excluir.")
        elif env in ("dev", "hml") and cat in ("compute", "db", "k8s") and svc != "Exadata Database Service" and rnd.random() < 0.75:
            o = mk_opp(r, "off_hours", rnd.uniform(0.55, 0.65), cost_ref, f"Desligar {r['name']} fora do expediente",
                       f"Ambiente {env} ativo 24x7; agendar desligamento noturno e em fins de semana.")
        elif cat in ("compute", "db", "k8s") and r["cpu"] and 5 <= r["cpu"] < 25 and rnd.random() < 0.7:
            o = mk_opp(r, "rightsizing", rnd.uniform(0.25, 0.45), cost_ref, f"Rightsizing de {r['name']}",
                       f"CPU média de {r['cpu']:.0f}%; reduzir uma ou duas famílias de tamanho em {svc}.")
        elif cat == "object" and rnd.random() < 0.6:
            o = mk_opp(r, "storage_tiering", rnd.uniform(0.30, 0.55), cost_ref, f"Tiering de dados frios em {r['name']}",
                       "Parcela relevante dos objetos sem acesso há mais de 90 dias; aplicar lifecycle para classe fria.")
        elif cat == "logs" and rnd.random() < 0.8:
            o = mk_opp(r, "log_retention", rnd.uniform(0.35, 0.55), cost_ref, f"Reduzir retenção de logs em {r['name']}",
                       "Retenção acima do necessário e logs de baixo valor; revisar com Segurança/Compliance.")
        elif cat in ("compute", "db") and r["arch"] == "x86" and env != "dev" and rnd.random() < {
                "aws": 0.5, "azure": 0.2, "oci": 0.2, "gcp": 0.15, "huawei": 0.25}[r["cloud"]]:
            arch = {"aws": "Graviton", "azure": "Ampere/Cobalt", "oci": "Ampere A1", "gcp": "Tau T2A",
                    "huawei": "Kunpeng"}[r["cloud"]]
            o = mk_opp(r, "graviton", rnd.uniform(0.15, 0.22), cost_ref, f"Migrar {r['name']} para {arch}",
                       f"Carga compatível com ARM; avaliar migração para {arch} com teste de desempenho.")
        elif cat in ("compute", "db") and env == "prod" and cost_ref > 4000 and rnd.random() < 0.14:
            o = mk_opp(r, "modernization", rnd.uniform(0.25, 0.40), cost_ref, f"Modernizar {r['name']}",
                       "Candidato a serviço gerenciado, containers ou serverless; exige refatoração.")
        if o and o["status"] == "Capturada":
            o["captured_k"] = rnd.randint(3, 11)

    # ---- aplica reducao de custo de oportunidades capturadas e marca otimizados
    for o in opps:
        if o["status"] == "Capturada":
            r = o["resource"]
            r["captured_k"], r["cap_pct"] = o["captured_k"], o["pct"] / 100
            r["is_optimized"] = True
            if o["typ"] in ("idle_resources", "orphan_resources"):
                r["is_idle"] = r["is_orphan"] = False
                r["cap_zero"] = True

    # ---- insere recursos e custos
    res_rows, cost_rows = [], []
    for r in res:
        res_rows.append((r["id"], r["account_id"], r["company_id"], r["cloud"], r["service"], r["rtype"], r["name"],
                         r["region"], r["environment"], r["owner"], r["product_id"], r["application_id"],
                         r["cost_center_id"], json.dumps(r["tags"], ensure_ascii=False),
                         "terminated" if r["end_k"] < 11 else r["state"], r["cpu"], r["arch"], r["is_idle"],
                         r["is_orphan"], r["is_optimized"], r["naming_ok"], r["created"], r["retired"]))
    copy("resource", ["id", "account_id", "company_id", "cloud_code", "service", "resource_type", "resource_name",
                      "region", "environment", "owner", "product_id", "application_id", "cost_center_id", "tags",
                      "state", "cpu_avg", "arch", "is_idle", "is_orphan", "is_optimized", "naming_ok", "created_at",
                      "retired_at"], res_rows)
    cur.execute("SELECT setval(pg_get_serial_sequence('resource','id'), (SELECT max(id) FROM resource))")
    monthly_actual = {c: [0.0] * 12 for c in comp}
    for r in res:
        c = comp[r["company"]]
        for k in range(12):
            v = cost_at(r, c, k)
            if v <= 0:
                continue
            if r["captured_k"] is not None and k >= r["captured_k"]:
                v *= (1 - r["cap_pct"])
            if v < 0.5:
                continue
            monthly_actual[r["company"]][k] += v
            qty = v / UNIT_PRICE.get(r["cat"], 1.0)
            cost_rows.append((r["id"], months[k], round(v, 2), round(qty, 2), UNIT_NAME.get(r["cat"], "unidades")))
    copy("cost_monthly", ["resource_id", "month", "cost_brl", "usage_qty", "usage_unit"], cost_rows)
    log(f"linhas de custo: {len(cost_rows)}")

    # ---- custos compartilhados
    pool_rows, pcost_rows = [], []
    direct_snapshot = {code: list(v) for code, v in monthly_actual.items()}   # custo direto por empresa/mes
    shared_total = TOTAL_REF_MONTH * SHARED_SHARE_OF_TOTAL
    for i, (code, name, desc, share) in enumerate(SHARED_POOLS, start=1):
        pool_rows.append((i, comp["simpar"]["id"], code, name, None, desc))
        for k in range(12):
            v = shared_total * share * (1.008 ** (k - 11)) * rnd.lognormvariate(0, 0.02)
            pcost_rows.append((i, months[k], round(v, 2)))
            dsum = sum(direct_snapshot[cc][k] for cc in comp)
            for cc in comp:                       # budget considera o custo com rateio proporcional
                monthly_actual[cc][k] += v * direct_snapshot[cc][k] / dsum
    copy("shared_pool", ["id", "company_id", "code", "name", "cloud_code", "description"], pool_rows)
    copy("shared_cost_monthly", ["pool_id", "month", "cost_brl"], pcost_rows)
    rules = [(1, "proportional", "{}"), (2, "even", "{}"), (3, "proportional", "{}"),
             (4, "fixed", json.dumps({"simpar": 0.20, "movida": 0.25, "jsl": 0.20, "vamos": 0.12, "automob": 0.07,
                                      "csinfra": 0.08, "csbrasil": 0.08})),
             (5, "proportional", "{}")]
    copy("allocation_rule", ["pool_id", "method", "weights"], rules)

    # ---- budget (plano com crescimento uniforme; vies por empresa)
    bud_rows = []
    for c in comp.values():
        b0 = monthly_actual[c["code"]][0] * (1 + c["bias"])
        for i, m in enumerate(budget_months):
            bud_rows.append((c["id"], m, round(b0 * (1.010 ** i), 2)))
    copy("budget", ["company_id", "month", "amount_brl"], bud_rows)

    # ---- compromissos (SP/RI/CUD...) e cobertura
    commit_rows, cov = [], {}
    cid = 0
    for c in comp.values():
        for cloud in c["mix"]:
            rs = [r for r in res if r["company"] == c["code"] and r["cloud"] == cloud and r["cat"] in ("compute", "db")
                  and r["end_k"] == 11 and r["env"] == "prod"]
            spend = sum(cost_at(r, c, 11) for r in rs)
            if spend < 20000:
                continue
            prod_acc = next(a for a, s in accounts[(c["code"], cloud)] if s == "prod")
            kinds = COMMITMENT_KINDS[cloud][: 1 + (1 if rnd.random() < 0.7 else 0)]
            covs = []
            for kind, term in kinds:
                cid += 1
                coverage = rnd.uniform(22, 68)
                util = rnd.uniform(80, 99)
                covs.append(coverage)
                commit_rows.append((cid, c["id"], prod_acc, cloud, kind, term,
                                    round(spend * coverage / 100 * 0.6 / len(kinds), 2), round(coverage, 2),
                                    round(util, 2), add_months(ref, rnd.randint(2, 30))))
            cov[(c["code"], cloud)] = (sum(covs) / len(covs) / 100, spend, prod_acc)
    copy("commitment", ["id", "company_id", "account_id", "cloud_code", "kind", "term_months", "monthly_commit_brl",
                        "coverage_pct", "utilization_pct", "expires_on"], commit_rows)

    # ---- oportunidades de compromisso (nivel de conta) com cobertura alvo de 80%
    class _R(dict):
        pass

    for (ccode, cloud), (coverage, spend, acc) in cov.items():
        gap = max(0.0, 0.85 - coverage)
        if gap < 0.04:
            continue
        comp_c = comp[ccode]
        for typ, share_, disc, label in (("savings_plans", 0.7, 0.26, "compromisso de compute"),
                                         ("reserved_instances", 0.3, 0.33, "reservas de banco de dados")):
            base_cost = spend * gap * share_
            if base_cost < 5000:
                continue
            fake = {"company": ccode, "company_id": comp_c["id"], "cloud": cloud, "account_id": acc, "id": None,
                    "owner": "Squad FinOps", "env": "prod"}
            o = mk_opp(fake, typ, disc, base_cost,
                       f"Ampliar cobertura de {label} em {cloud.upper()} ({ccode})",
                       f"Cobertura atual de {coverage * 100:.0f}% para meta de 85%; elevar compromissos sobre carga estável.")
            o["rid"] = None
            o["resource"] = None
            if o["status"] == "Capturada":
                o["captured_k"] = rnd.randint(4, 11)

    # ---- score de prioridade, inserts de oportunidades e economia capturada
    savs = sorted(o["sav"] for o in opps)
    s95 = savs[int(len(savs) * 0.95)] if savs else 1.0
    now = datetime.now(timezone.utc)
    opp_rows, cap_rows = [], []
    for i, o in enumerate(opps, start=1):
        o["id"] = i
        score = 100 * (0.5 * min(1.0, o["sav"] / s95) + 0.25 * (1 - (EFFORT_I[o["effort"]] - 1) / 2)
                       + 0.15 * (1 - (EFFORT_I[o["risk"]] - 1) / 2) + 0.10 * (1 - min(o["term"], 180) / 180))
        cmonth = months[o["captured_k"]] if o["captured_k"] is not None else None
        opp_rows.append((i, o["company_id"], o["cloud"], o["account_id"], o["rid"], o["typ"], o["title"], o["desc"],
                         round(o["cost"], 2), round(o["sav"], 2), round(o["pct"], 2), o["effort"], o["term"], o["risk"],
                         round(score, 2), o["status"], o["owner"], cmonth, now))
        if cmonth:
            for k in range(o["captured_k"], 12):
                cap_rows.append((months[k], i, o["company_id"], o["cloud"], o["typ"], round(o["sav"], 2)))
    copy("opportunity", ["id", "company_id", "cloud_code", "account_id", "resource_id", "opp_type", "title",
                         "description", "current_cost_brl", "savings_monthly_brl", "savings_pct", "effort", "term_days",
                         "risk", "priority_score", "status", "owner", "captured_month", "created_at"], opp_rows)
    cur.execute("SELECT setval(pg_get_serial_sequence('opportunity','id'), (SELECT max(id) FROM opportunity))")
    copy("savings_captured", ["month", "opportunity_id", "company_id", "cloud_code", "opp_type", "amount_brl"], cap_rows)

    # ---- conexoes (modo demo) e execucoes de ETL
    conn_rows, etl_rows, n = [], [], 0
    for c in comp.values():
        for cloud in c["mix"]:
            n += 1
            ok = rnd.random() > 0.08
            conn_rows.append((n, c["id"], cloud, f"{c['name']} · {dict((x[0], x[1]) for x in CLOUDS)[cloud]}",
                              {"aws": "IAM Role (AssumeRole)", "azure": "Service Principal", "oci": "API Key",
                               "gcp": "Service Account", "huawei": "AK/SK"}[cloud],
                              json.dumps({"accounts": len(accounts[(c["code"], cloud)])}), None, "demo",
                              "connected" if ok else "error", True,
                              now - timedelta(hours=rnd.randint(1, 20)),
                              "Sincronização de demonstração concluída" if ok else "Credencial expirada (simulado)", now))
            for h in range(3):
                etl_rows.append((n, now - timedelta(days=h, hours=2), now - timedelta(days=h, hours=2) + timedelta(minutes=3),
                                 "success" if (ok or h > 0) else "error", rnd.randint(2000, 9000), rnd.randint(100, 900),
                                 rnd.randint(5, 80), "ok"))
    copy("cloud_connection", ["id", "company_id", "cloud_code", "display_name", "auth_type", "config", "secret_enc", "mode",
                              "status", "sync_enabled", "last_sync_at", "last_message", "created_at"], conn_rows)
    cur.execute("SELECT setval(pg_get_serial_sequence('cloud_connection','id'), (SELECT max(id) FROM cloud_connection))")
    copy("etl_run", ["connection_id", "started_at", "finished_at", "status", "rows_cost", "rows_resources", "rows_recs",
                     "message"], etl_rows)

    raw.commit()
    raw.close()
    summary = dict(reference_month=ref.isoformat(), resources=len(res), cost_rows=len(cost_rows),
                   opportunities=len(opps), commitments=len(commit_rows), connections=n)
    log("seed concluido:", summary)
    return summary
