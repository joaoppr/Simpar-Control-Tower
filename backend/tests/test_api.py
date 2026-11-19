"""Testes de fumaca: exigem o banco carregado (python -m app.seed)."""
from datetime import date

from fastapi.testclient import TestClient

from app.connectors.aws import AwsConnector
from app.main import app
from app.services.common import forecast

c = TestClient(app)


def test_meta_and_executive():
    m = c.get("/api/meta").json()
    assert len(m["companies"]) == 7 and len(m["clouds"]) == 5
    d = c.get("/api/executive/overview").json()
    assert d["kpis"]["total_spend"] > 0 and len(d["trend"]) == 15 and len(d["top_consumers"]) == 20
    assert abs(sum(x["cost"] for x in d["by_company"]) - d["kpis"]["total_spend"]) < 1


def test_company_sums_to_group():
    total = c.get("/api/executive/overview").json()["kpis"]["total_spend"]
    s = sum(c.get(f"/api/company/{x['code']}/overview").json()["kpis"]["total_spend"] for x in c.get("/api/meta").json()["companies"])
    assert abs(s - total) < 1


def test_showback_allocation_conserves_cost():
    p = c.get("/api/showback/pools").json()
    for pool in p["pools"]:
        assert abs(sum(a["amount"] for a in pool["allocation"]) - pool["cost"]) < 1
    st = c.get("/api/showback/statements").json()
    assert abs(st["totals"]["total"] - c.get("/api/executive/overview").json()["kpis"]["total_spend"]) < 5


def test_opportunities_no_double_count():
    s = c.get("/api/opportunities/summary").json()
    assert s["total_monthly"] > 0 and {t["priority"] for t in s["types"]} <= {"P1", "P2", "P3"}


def test_governance_and_inventory():
    g = c.get("/api/governance/summary").json()
    assert 0 < g["maturity_group"]["score"] <= 100
    assert c.get("/api/inventory?page_size=5").json()["total"] > 100


def test_copilot_offline():
    r = c.post("/api/copilot/chat", json={"message": "Qual a maior oportunidade de economia da JSL?"}).json()
    assert r["tool"] == "top_opportunities" and "JSL" in r["text"]


def test_forecast_shape():
    f = forecast([100, 102, 104, 106, 108, 110, 112], 3)
    assert len(f) == 3 and f[0]["value"] > 112 and f[0]["low"] <= f[0]["value"] <= f[0]["high"]


def test_aws_cost_normalization():
    class CE:
        def get_cost_and_usage(self, **kw):
            return {"ResultsByTime": [{"TimePeriod": {"Start": "2026-09-01"}, "Groups": [
                {"Keys": ["123456789012", "Amazon EC2"], "Metrics": {"UnblendedCost": {"Amount": "10.5", "Unit": "USD"}}}]}]}

    class S:
        def client(self, n):
            return CE()

    a = AwsConnector({}, {})
    a._session = lambda: S()
    out = a.fetch_costs(date(2026, 9, 1), date(2026, 10, 1))
    assert out == [{"month": date(2026, 9, 1), "account": "123456789012", "service": "Amazon EC2", "cost": 10.5, "currency": "USD", "tags": {}}]
