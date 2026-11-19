from datetime import date

from .base import CloudConnector


class HuaweiConnector(CloudConnector):
    cloud = "huawei"
    cost_source = "Huawei Cloud BSS (Billing) API"
    fields = [("ak", "Access Key (AK)", False, ""), ("sk", "Secret Key (SK)", True, ""),
              ("domain_id", "Domain ID", False, ""), ("endpoint", "Endpoint BSS", False, "https://bss-intl.myhuaweicloud.com")]

    def _client(self):
        core = self.need("huaweicloudsdkcore.auth.credentials", "huaweicloudsdkcore")
        bss = self.need("huaweicloudsdkbss.v2", "huaweicloudsdkbss")
        cred = core.GlobalCredentials(self.cfg["ak"], self.sec["sk"], self.cfg.get("domain_id"))
        return bss, bss.BssClient.new_builder().with_credentials(cred).with_endpoint(self.cfg.get("endpoint", "https://bss-intl.myhuaweicloud.com")).build()

    def test(self):
        bss, cl = self._client()
        cl.show_customer_account_balances(bss.ShowCustomerAccountBalancesRequest())
        return True, "API BSS acessível"

    def fetch_costs(self, start: date, end: date):
        bss, cl = self._client()
        out, cur = [], start.replace(day=1)
        while cur <= end:
            req = bss.ListCustomerselfResourceRecordsRequest()
            req.cycle, req.limit = cur.strftime("%Y-%m"), 100
            r = cl.list_customerself_resource_records(req)
            for x in (r.fee_records or []):
                out.append({"month": cur, "account": self.cfg.get("domain_id", ""), "service": x.cloud_service_type_name or x.cloud_service_type,
                            "cost": float(x.official_amount or 0), "currency": r.currency or "BRL", "tags": {}})
            cur = date(cur.year + (cur.month // 12), cur.month % 12 + 1, 1)
        return out
