"""Ferramentas de dados do Copilot FinOps. Cada ferramenta consulta o banco e devolve
{"text": resposta em PT-BR, "table": {"columns": [...], "rows": [...]} | None, "data": {...}}.
As mesmas ferramentas servem ao modo offline (roteador por palavras-chave) e ao modo OpenAI (function calling)."""
from __future__ import annotations

from datetime import date

from ..db import q, q1
from . import kpis as K
from .common import add_months, brl, brl_compact, month_range, org_id, pct, reference_month
from .maturity import group_maturity, maturity

MONTH_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def mlabel(m: date) -> str:
    return f"{MONTH_PT[m.month - 1]}/{m.year}"


def _who(company: str | None) -> str:
    if not company:
        return "o Grupo Simpar"
    return q1("SELECT name FROM dim_company WHERE org_id=:o AND code=:c", o=org_id(), c=company).get("name", company)


def _de(company: str | None) -> str:
    return "do Grupo Simpar" if not company else f"de {_who(company)}"


def _subj(company: str | None) -> str:
    w = _who(company)
    return w[0].upper() + w[1:]


def _cloud(cloud: str | None) -> str:
    return q1("SELECT name FROM dim_cloud WHERE code=:c", c=cloud).get("name", cloud) if cloud else ""


def spend(company=None, cloud=None, month: date | None = None, **_):
    m = month or reference_month()
    k = K.kpi_block(m, company, cloud)
    where = " AND company_code=:co" if company else ""
    rows = K.breakdown("cloud" if not cloud else "service", m, company, cloud, 8)
    cl = f" em {_cloud(cloud)}" if cloud else ""
    txt = (f"{_subj(company)} gastou **{brl(k['total_spend'])}**{cl} em {mlabel(m)}"
           + (f" ({k['mom_pct']:+.1f}% vs. mês anterior)" if k["mom_pct"] is not None else "") + ".")
    if not cloud and company:
        txt += f" Desse total, {brl(k['shared_allocated'])} são custos compartilhados rateados."
    if k["budget"] and not cloud:
        txt += f" O budget do mês era {brl(k['budget'])} ({k['budget_var_pct']:+.1f}%)."
    return {"text": txt, "table": {"columns": ["Item", "Custo (R$)", "%"], "rows": [[r["name"], r["cost"], r["share"]] for r in rows]},
            "data": k}


def top_opportunities(company=None, cloud=None, limit: int = 5, **_):
    w, p = "org_id=:o AND status <> 'Capturada'", dict(o=org_id(), lim=limit)
    for col, v, key in (("company_code", company, "co"), ("cloud_code", cloud, "cl")):
        if v:
            w += f" AND {col}=:{key}"
            p[key] = v
    types = q(f"""SELECT opp_type, SUM(savings_monthly_brl) AS s, COUNT(*) AS n FROM v_opportunity WHERE {w}
                  GROUP BY 1 ORDER BY s DESC LIMIT 1""", **p)
    items = q(f"""SELECT title, opp_type, cloud_code, savings_monthly_brl, effort, term_days, risk FROM v_opportunity
                  WHERE {w} ORDER BY savings_monthly_brl DESC LIMIT :lim""", **p)
    from ..seed.catalog import OPP_TYPE_NAME
    tot = q1(f"SELECT SUM(savings_monthly_brl) AS s FROM v_opportunity WHERE {w}", **p)["s"] or 0
    if not types:
        return {"text": f"Não há oportunidades abertas para {_who(company)}.", "table": None, "data": {}}
    t = types[0]
    txt = (f"A maior oportunidade {_de(company)} é **{OPP_TYPE_NAME[t['opp_type']]}**, com potencial de "
           f"**{brl(t['s'])}/mês** ({brl(t['s'] * 12)}/ano) em {t['n']} itens. O potencial total em aberto é {brl(tot)}/mês.")
    return {"text": txt, "table": {"columns": ["Oportunidade", "Cloud", "Economia/mês (R$)", "Esforço", "Prazo (d)", "Risco"],
                                   "rows": [[i["title"], i["cloud_code"].upper(), i["savings_monthly_brl"], i["effort"], i["term_days"], i["risk"]] for i in items]},
            "data": {"total_monthly": tot}}


def untagged(company=None, cloud=None, limit: int = 10, **_):
    m = reference_month()
    w, p = "org_id=:o AND month=:m AND NOT fully_tagged", dict(o=org_id(), m=m, lim=limit)
    for col, v, key in (("company_code", company, "co"), ("cloud_code", cloud, "cl")):
        if v:
            w += f" AND {col}=:{key}"
            p[key] = v
    t = q1(f"SELECT COUNT(*) AS n, COALESCE(SUM(cost_brl),0) AS c FROM v_cost WHERE {w}", **p)
    all_ = q1("SELECT COUNT(*) AS n FROM v_cost WHERE org_id=:o AND month=:m" + (" AND company_code=:co" if company else ""), o=org_id(), m=m, co=company)["n"]
    rows = q(f"""SELECT resource_name, cloud_code, service, cost_brl, owner IS NULL AS no_owner, product_id IS NULL AS no_product,
                        cost_center_id IS NULL AS no_cc FROM v_cost WHERE {w} ORDER BY cost_brl DESC LIMIT :lim""", **p)
    txt = (f"{_subj(company)} possui **{t['n']} recursos sem conformidade de tags** ({pct(t['n'], all_):.0f}% do inventário), "
           f"somando {brl(t['c'])}/mês. Abaixo, os de maior custo.")
    return {"text": txt, "table": {"columns": ["Recurso", "Cloud", "Serviço", "Custo (R$)", "Sem owner", "Sem produto", "Sem C. custo"],
                                   "rows": [[r["resource_name"], r["cloud_code"].upper(), r["service"], r["cost_brl"], "sim" if r["no_owner"] else "", "sim" if r["no_product"] else "", "sim" if r["no_cc"] else ""] for r in rows]},
            "data": t}


def group_potential(company=None, **_):
    k = K.kpi_block(reference_month(), company)
    bt = q("""SELECT opp_type, SUM(savings_monthly_brl) AS s FROM v_opportunity WHERE org_id=:o AND status <> 'Capturada'""" +
           (" AND company_code=:co" if company else "") + " GROUP BY 1 ORDER BY 2 DESC LIMIT 5", o=org_id(), co=company)
    from ..seed.catalog import OPP_TYPE_NAME
    txt = (f"O potencial de saving {_de(company)} é **{brl(k['saving_potential'])}/mês** ({brl(k['saving_potential'] * 12)}/ano), "
           f"equivalente a {k['saving_potential_pct']:.1f}% do gasto mensal. Já foram capturados {brl(k['saving_captured_month'])}/mês "
           f"({brl(k['saving_captured_ytd'])} no ano). Valores simulados; economia só é considerada realizada após validação de Finanças.")
    return {"text": txt, "table": {"columns": ["Alavanca", "Potencial/mês (R$)"], "rows": [[OPP_TYPE_NAME[r["opp_type"]], r["s"]] for r in bt]}, "data": k}


def idle(company=None, **_):
    k = K.kpi_block(reference_month(), company)
    rows = q("""SELECT resource_name, company_name, cloud_code, service, cost_brl FROM v_cost WHERE org_id=:o AND month=:m AND (is_idle OR is_orphan)""" +
             (" AND company_code=:co" if company else "") + " ORDER BY cost_brl DESC LIMIT 10", o=org_id(), m=reference_month(), co=company)
    return {"text": f"{_subj(company)} tem **{k['idle_resources']} recursos ociosos ou órfãos** ({k['idle_pct']:.1f}% do custo, {brl(k['idle_cost'])}/mês).",
            "table": {"columns": ["Recurso", "Empresa", "Cloud", "Serviço", "Custo (R$)"], "rows": [[r["resource_name"], r["company_name"], r["cloud_code"].upper(), r["service"], r["cost_brl"]] for r in rows]}, "data": k}


def forecast_tool(company=None, **_):
    tr = [t for t in K.trend(company) if t["actual"] is None]
    return {"text": f"Forecast {_de(company)} para os próximos 3 meses: " + "; ".join(f"{mlabel(date.fromisoformat(t['month']))}: {brl_compact(t['forecast'])}" for t in tr) + ".",
            "table": {"columns": ["Mês", "Forecast (R$)", "Faixa baixa", "Faixa alta", "Budget (R$)"],
                      "rows": [[t["month"][:7], t["forecast"], t["forecast_low"], t["forecast_high"], t["budget"]] for t in tr]}, "data": {}}


def budget(company=None, **_):
    rows = [c for c in K.company_table(reference_month()) if not company or c["code"] == company]
    tot_a, tot_b = sum(r["cost"] for r in rows), sum(r["budget"] for r in rows)
    var = (tot_a / tot_b - 1) * 100 if tot_b else 0
    return {"text": f"Em {mlabel(reference_month())}, {_who(company)} realizou {brl(tot_a)} contra budget de {brl(tot_b)} ({var:+.1f}%).",
            "table": {"columns": ["Empresa", "Realizado (R$)", "Budget (R$)", "Variação %"], "rows": [[r["name"], r["cost"], r["budget"], r["variance_pct"]] for r in rows]}, "data": {}}


def top_consumers(company=None, limit: int = 10, **_):
    rows = K.top_consumers(reference_month(), "application", limit, company)
    return {"text": f"Maiores consumidores {_de(company)} em {mlabel(reference_month())}:",
            "table": {"columns": ["#", "Aplicação", "Empresa", "Cloud", "Custo (R$)", "%"], "rows": [[r["rank"], r["name"], r["company_name"], r["cloud_code"], r["cost"], r["share"]] for r in rows]}, "data": {}}


def maturity_tool(company=None, **_):
    m = reference_month()
    mat = maturity(m)
    grp = group_maturity(m, mat)
    sel = next((x for x in mat if x["code"] == company), None) if company else grp
    rows = [[x["name"], x["score"], x["level"]] for x in ([sel] if sel else mat)]
    return {"text": f"Score de maturidade FinOps {_de(company)}: **{sel['score']:.0f}/100 ({sel['level']})**." if sel else "Ranking de maturidade por empresa:",
            "table": {"columns": ["Empresa", "Score", "Nível"], "rows": [[x["name"], x["score"], x["level"]] for x in mat] if not company else rows}, "data": {}}


def coverage(company=None, **_):
    k = K.kpi_block(reference_month(), company)
    return {"text": (f"Cobertura {_de(company)}: tags **{k['tag_coverage']:.1f}%**, showback **{k['showback_coverage']:.1f}%**, "
                     f"chargeback **{k['chargeback_coverage']:.1f}%** do custo direto."), "table": None, "data": k}


TOOLS = {"spend": spend, "top_opportunities": top_opportunities, "untagged": untagged, "group_potential": group_potential, "idle": idle,
         "forecast": forecast_tool, "budget": budget, "top_consumers": top_consumers, "maturity": maturity_tool, "coverage": coverage}

_P = {"company": {"type": "string", "description": "código da empresa: simpar, movida, jsl, vamos, automob, csinfra, csbrasil (omitir para o grupo)"},
      "cloud": {"type": "string", "description": "aws, azure, oci, gcp ou huawei (opcional)"}}
TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": n, "description": d, "parameters": {"type": "object", "properties": props}}}
    for n, d, props in [
        ("spend", "Custo de um mês (padrão: mês de referência) por empresa/cloud, com quebra por cloud ou serviço", {**_P, "month": {"type": "string", "description": "YYYY-MM"}}),
        ("top_opportunities", "Maiores oportunidades de economia abertas", {**_P, "limit": {"type": "integer"}}),
        ("untagged", "Recursos sem conformidade de tags", {**_P, "limit": {"type": "integer"}}),
        ("group_potential", "Potencial de saving (e saving capturado)", {"company": _P["company"]}),
        ("idle", "Recursos ociosos ou órfãos", {"company": _P["company"]}),
        ("forecast", "Forecast dos próximos 3 meses", {"company": _P["company"]}),
        ("budget", "Budget x realizado", {"company": _P["company"]}),
        ("top_consumers", "Maiores consumidores (aplicações)", {"company": _P["company"], "limit": {"type": "integer"}}),
        ("maturity", "Score de maturidade FinOps", {"company": _P["company"]}),
        ("coverage", "Cobertura de tags, showback e chargeback", {"company": _P["company"]}),
    ]]
