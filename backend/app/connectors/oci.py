from datetime import date, datetime, timezone

from .base import CloudConnector


class OciConnector(CloudConnector):
    cloud = "oci"
    cost_source = "OCI Usage API (RequestSummarizedUsages)"
    fields = [("tenancy", "Tenancy OCID", False, "ocid1.tenancy.oc1..."), ("user", "User OCID", False, "ocid1.user.oc1..."),
              ("fingerprint", "Fingerprint da API key", False, ""), ("region", "Região home", False, "sa-saopaulo-1"),
              ("private_key", "Chave privada (PEM)", True, "")]

    def _cfg(self):
        return {"user": self.cfg["user"], "tenancy": self.cfg["tenancy"], "fingerprint": self.cfg["fingerprint"],
                "region": self.cfg["region"], "key_content": self.sec["private_key"]}

    def test(self):
        oci = self.need("oci", "oci")
        cfg = self._cfg()
        oci.config.validate_config(cfg)
        t = oci.identity.IdentityClient(cfg).get_tenancy(cfg["tenancy"]).data
        return True, f"Tenancy '{t.name}' acessível"

    def fetch_costs(self, start: date, end: date):
        oci = self.need("oci", "oci")
        cl = oci.usage_api.UsageapiClient(self._cfg())
        d = oci.usage_api.models.RequestSummarizedUsagesDetails(
            tenant_id=self.cfg["tenancy"], granularity="MONTHLY", query_type="COST", group_by=["service", "compartmentName"],
            time_usage_started=datetime(start.year, start.month, start.day, tzinfo=timezone.utc),
            time_usage_ended=datetime(end.year, end.month, end.day, tzinfo=timezone.utc))
        out = []
        for it in cl.request_summarized_usages(d).data.items:
            out.append({"month": it.time_usage_started.date().replace(day=1), "account": it.compartment_name or self.cfg["tenancy"],
                        "service": it.service, "cost": float(it.computed_amount or 0), "currency": it.currency or "BRL", "tags": {}})
        return out

    def fetch_resources(self):
        oci = self.need("oci", "oci")
        cl = oci.resource_search.ResourceSearchClient(self._cfg())
        res = cl.search_resources(oci.resource_search.models.StructuredSearchDetails(
            type="Structured", query="query all resources")).data.items
        return [{"account": r.compartment_id, "service": r.resource_type, "type": r.resource_type, "name": r.display_name,
                 "region": self.cfg["region"], "tags": {**(r.freeform_tags or {})}, "monthly_cost": None} for r in res]
