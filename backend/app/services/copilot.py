"""Roteamento do Copilot: OpenAI (function calling) quando ha chave; caso contrario NLU offline por palavras-chave."""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import date

import httpx

from ..config import settings
from ..db import q
from .common import add_months, org_id, reference_month
from .copilot_tools import MONTH_PT, TOOL_SCHEMAS, TOOLS

CLOUD_ALIASES = {"aws": ["aws", "amazon"], "azure": ["azure", "microsoft"], "oci": ["oci", "oracle"], "gcp": ["gcp", "google"], "huawei": ["huawei"]}
COMPANY_ALIASES = {"simpar": ["simpar"], "movida": ["movida"], "jsl": ["jsl"], "vamos": ["vamos"], "automob": ["automob"],
                   "csinfra": ["csinfra", "cs infra"], "csbrasil": ["csbrasil", "cs brasil"]}
SYSTEM = ("Você é o Copilot FinOps do Grupo Simpar. Responda em português do Brasil, de forma executiva e concisa, "
          "SOMENTE com dados retornados pelas ferramentas. Os dados são de demonstração (fictícios). Se faltar dado, diga isso.")


def _norm(s: str) -> str:
    return unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode()


def parse_entities(text: str) -> dict:
    t = _norm(text)
    company = next((c for c, al in COMPANY_ALIASES.items() if any(re.search(rf"\b{re.escape(a)}\b", t) for a in al)), None)
    cloud = next((c for c, al in CLOUD_ALIASES.items() if any(re.search(rf"\b{a}\b", t) for a in al)), None)
    ref = reference_month()
    month = None
    if "mes passado" in t or "mes anterior" in t:
        month = add_months(ref, -1)
    else:
        for i, mn in enumerate(MONTH_PT):
            if re.search(rf"\b{_norm(mn)}\b", t) or re.search(rf"\b{_norm(mn)[:3]}\b", t):
                y = ref.year if i + 1 <= ref.month else ref.year - 1
                month = date(y, i + 1, 1)
                break
    return {"company": company, "cloud": cloud, "month": month}


def route_offline(text: str) -> tuple[str, dict]:
    t = _norm(text)
    e = parse_entities(text)
    if any(k in t for k in ("sem tag", "sem owner", "tag", "sem produto", "sem centro")):
        return "untagged", e
    if any(k in t for k in ("ocios", "orfao", "sem uso", "desperdicio")):
        return "idle", e
    if any(k in t for k in ("maturidade", "score")):
        return "maturity", e
    if any(k in t for k in ("cobertura", "showback", "chargeback")):
        return "coverage", e
    if any(k in t for k in ("forecast", "previsao", "projecao", "proximos meses")):
        return "forecast", e
    if any(k in t for k in ("budget", "orcamento", "meta")):
        return "budget", e
    if any(k in t for k in ("top", "maiores consumidores", "maior consumo", "quem mais gasta", "ranking")):
        return "top_consumers", e
    if any(k in t for k in ("potencial", "quanto posso economizar", "saving")) and not any(k in t for k in ("maior oportunidade",)):
        return "group_potential", e
    if any(k in t for k in ("oportunidade", "economia", "economizar", "otimiz")):
        return "top_opportunities", e
    if any(k in t for k in ("gast", "custo", "consumo", "spend", "quanto")):
        return "spend", e
    return "help", e


HELP = ("Posso responder sobre custos, oportunidades, tags, ociosos, forecast, budget, maturidade e cobertura. Exemplos: "
        "\"Quanto a Movida gastou em AWS este mês?\", \"Qual a maior oportunidade de economia da JSL?\", "
        "\"Quais recursos sem tag existem na Vamos?\", \"Qual o potencial de saving do grupo?\"")


def _clean(args: dict) -> dict:
    out = {k: v for k, v in args.items() if v not in (None, "")}
    if isinstance(out.get("month"), str):
        y, m = out["month"][:7].split("-")
        out["month"] = date(int(y), int(m), 1)
    return out


def answer(message: str, history: list[dict] | None = None) -> dict:
    if settings.openai_api_key:
        try:
            return _answer_openai(message, history or [])
        except Exception as ex:  # cai para o modo offline sem quebrar a demo
            res = _offline(message)
            res["text"] += f"\n\n_(OpenAI indisponível: {str(ex)[:80]}; resposta gerada em modo offline.)_"
            return res
    return _offline(message)


def _offline(message: str) -> dict:
    tool, ent = route_offline(message)
    if tool == "help":
        return {"mode": "offline", "tool": None, "text": HELP, "table": None}
    r = TOOLS[tool](**{k: v for k, v in ent.items() if v})
    return {"mode": "offline", "tool": tool, "text": r["text"], "table": r["table"]}


def _answer_openai(message: str, history: list[dict]) -> dict:
    msgs = [{"role": "system", "content": SYSTEM}] + [{"role": h["role"], "content": h["content"]} for h in history[-6:]] + [{"role": "user", "content": message}]
    table, used = None, None
    for _ in range(3):
        r = httpx.post("https://api.openai.com/v1/chat/completions", timeout=60,
                       headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                       json={"model": settings.openai_model, "messages": msgs, "tools": TOOL_SCHEMAS, "temperature": 0.2})
        r.raise_for_status()
        m = r.json()["choices"][0]["message"]
        if not m.get("tool_calls"):
            return {"mode": "openai", "tool": used, "text": m["content"], "table": table}
        msgs.append(m)
        for tc in m["tool_calls"]:
            fn = tc["function"]["name"]
            res = TOOLS[fn](**_clean(json.loads(tc["function"]["arguments"] or "{}")))
            table, used = res["table"] or table, fn
            msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": json.dumps({"text": res["text"], "table": res["table"]}, default=str, ensure_ascii=False)})
    return {"mode": "openai", "tool": used, "text": "Não consegui concluir a consulta.", "table": table}
