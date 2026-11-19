from datetime import date

from .base import CloudConnector

ARM = "https://management.azure.com"


class AzureConnector(CloudConnector):
    cloud = "azure"
    cost_source = "Azure Cost Management Query API"
    fields = [("tenant_id", "Tenant ID", False, ""), ("client_id", "Client ID (Service Principal)", False, ""),
              ("client_secret", "Client Secret", True, ""), ("subscription_id", "Subscription ID", False, "")]

    def _headers(self):
        ident = self.need("azure.identity", "azure-identity")
        tok = ident.ClientSecretCredential(self.cfg["tenant_id"], self.cfg["client_id"], self.sec["client_secret"]).get_token(f"{ARM}/.default")
        return {"Authorization": f"Bearer {tok.token}"}

    def _get(self, path, **params):
        import httpx
        r = httpx.get(f"{ARM}{path}", headers=self._headers(), params=params, timeout=60)
        r.raise_for_status()
        return r.json()

    def test(self):
        d = self._get(f"/subscriptions/{self.cfg['subscription_id']}", **{"api-version": "2022-12-01"})
        return True, f"Assinatura '{d.get('displayName')}' acessível"

    def fetch_costs(self, start: date, end: date):
        import httpx
        sub = self.cfg["subscription_id"]
        body = {"type": "ActualCost", "timeframe": "Custom",
                "timePeriod": {"from": start.isoformat() + "T00:00:00Z", "to": end.isoformat() + "T23:59:59Z"},
                "dataset": {"granularity": "Monthly", "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
                            "grouping": [{"type": "Dimension", "name": "ServiceName"}]}}
        r = httpx.post(f"{ARM}/subscriptions/{sub}/providers/Microsoft.CostManagement/query", params={"api-version": "2023-11-01"},
                       headers=self._headers(), json=body, timeout=120)
        r.raise_for_status()
        p = r.json()["properties"]
        cols = [c["name"] for c in p["columns"]]
        out = []
        for row in p["rows"]:
            d = dict(zip(cols, row))
            month = str(d.get("BillingMonth", d.get("UsageDate")))[:10]
            out.append({"month": date.fromisoformat(month[:8] + "01"), "account": sub, "service": d["ServiceName"],
                        "cost": float(d["Cost"]), "currency": d.get("Currency", "BRL"), "tags": {}})
        return out

    def fetch_resources(self):
        sub, out = self.cfg["subscription_id"], []
        d = self._get(f"/subscriptions/{sub}/resources", **{"api-version": "2021-04-01"})
        for x in d.get("value", []):
            out.append({"account": sub, "service": x["type"], "type": x["type"], "name": x["name"], "region": x.get("location"),
                        "tags": x.get("tags") or {}, "monthly_cost": None})
        return out

    def fetch_recommendations(self):
        sub = self.cfg["subscription_id"]
        d = self._get(f"/subscriptions/{sub}/providers/Microsoft.Advisor/recommendations",
                      **{"api-version": "2023-01-01", "$filter": "Category eq 'Cost'"})
        out = []
        for x in d.get("value", []):
            ep = x["properties"].get("extendedProperties", {})
            out.append({"account": sub, "service": x["properties"].get("impactedField", ""), "resource": x["properties"].get("resourceMetadata", {}).get("resourceId"),
                        "type": "rightsizing" if "Right-size" in x["properties"]["shortDescription"]["problem"] else "reserved_instances",
                        "title": x["properties"]["shortDescription"]["problem"],
                        "savings_monthly": float(ep.get("savingsAmount", 0)) / (12 if ep.get("savingsAmount") and ep.get("term") else 1),
                        "currency": ep.get("savingsCurrency", "USD")})
        return out
