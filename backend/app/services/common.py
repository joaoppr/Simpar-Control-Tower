"""Funcoes compartilhadas: tenant, meses, rateio de custos compartilhados, forecast e formatacao."""
from __future__ import annotations

import math
from datetime import date
from functools import lru_cache

from ..config import settings
from ..db import q, scalar


@lru_cache(maxsize=1)
def org_id() -> int:
    v = scalar("SELECT id FROM org WHERE code = :c", c=settings.org_code)
    if v is None:
        raise RuntimeError("Banco vazio: execute `python -m app.seed` para carregar os dados de demonstracao.")
    return v


def add_months(d: date, n: int) -> date:
    y = d.year + (d.month - 1 + n) // 12
    return date(y, (d.month - 1 + n) % 12 + 1, 1)


def reference_month() -> date:
    return scalar("SELECT max(month) FROM cost_monthly")


def parse_month(s: str | None) -> date:
    if not s:
        return reference_month()
    y, m = s[:7].split("-")
    return date(int(y), int(m), 1)


def month_range() -> list[date]:
    ref = reference_month()
    return [add_months(ref, -11 + i) for i in range(12)]


def brl(v: float | None, decimals: int = 0) -> str:
    v = v or 0.0
    s = f"{abs(v):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("-" if v < 0 else "") + "R$ " + s


def brl_compact(v: float | None) -> str:
    v = v or 0.0
    a = abs(v)
    sign = "-" if v < 0 else ""
    if a >= 1e6:
        return f"{sign}R$ {a / 1e6:,.2f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
    if a >= 1e3:
        return f"{sign}R$ {a / 1e3:,.0f} mil".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sign}R$ {a:,.0f}"


def pct(a: float, b: float) -> float:
    return round(100.0 * a / b, 2) if b else 0.0


def pct_change(cur: float, prev: float) -> float | None:
    return round(100.0 * (cur - prev) / prev, 2) if prev else None


# ---------------------------------------------------------------- rateio de custos compartilhados
def allocate(method: str, weights: dict, direct: dict[str, float], amount: float) -> dict[str, float]:
    codes = list(direct)
    if method == "even":
        w = {c: 1.0 for c in codes}
    elif method == "fixed" and weights:
        w = {c: float(weights.get(c, 0)) for c in codes}
    else:
        w = {c: direct[c] for c in codes}
    tot = sum(w.values()) or 1.0
    return {c: amount * w[c] / tot for c in codes}


def loaded_costs(months: list[date], company: str | None = None) -> dict[tuple[str, date], dict]:
    """Custo por empresa/mes = direto + rateio dos pools compartilhados (conforme regra de cada pool)."""
    oid = org_id()
    direct = q("""SELECT company_code, month, SUM(cost_brl) AS c FROM v_cost
                  WHERE org_id=:o AND month = ANY(:m) GROUP BY 1,2""", o=oid, m=months)
    pools = q("""SELECT pool_id, month, cost_brl, method, weights FROM v_shared_cost
                 WHERE org_id=:o AND month = ANY(:m)""", o=oid, m=months)
    out: dict[tuple[str, date], dict] = {}
    by_month: dict[date, dict[str, float]] = {}
    for r in direct:
        by_month.setdefault(r["month"], {})[r["company_code"]] = r["c"]
        out[(r["company_code"], r["month"])] = {"direct": r["c"], "shared": 0.0}
    for p in pools:
        d = by_month.get(p["month"], {})
        for c, v in allocate(p["method"], p["weights"] or {}, d, p["cost_brl"]).items():
            out[(c, p["month"])]["shared"] += v
    for v in out.values():
        v["total"] = v["direct"] + v["shared"]
    if company:
        out = {k: v for k, v in out.items() if k[0] == company}
    return out


# ---------------------------------------------------------------- forecast
def forecast(series: list[float], horizon: int = 3) -> list[dict]:
    """Tendencia linear amortecida sobre os 6 ultimos meses + banda de confianca (~80%)."""
    n = min(6, len(series))
    y = series[-n:]
    xs = list(range(n))
    mx, my = sum(xs) / n, sum(y) / n
    sxx = sum((x - mx) ** 2 for x in xs) or 1.0
    slope = sum((x - mx) * (v - my) for x, v in zip(xs, y)) / sxx
    icpt = my - slope * mx
    resid = [v - (icpt + slope * x) for x, v in zip(xs, y)]
    sd = math.sqrt(sum(r * r for r in resid) / max(1, n - 2))
    last3 = sum(series[-3:]) / min(3, len(series))
    out = []
    damp = 0.0
    for h in range(1, horizon + 1):
        damp += 0.85 ** h
        val = last3 + slope * (1 + damp)
        band = 1.28 * sd * math.sqrt(1 + 0.5 * h)
        out.append({"value": round(val, 2), "low": round(val - band, 2), "high": round(val + band, 2)})
    return out
