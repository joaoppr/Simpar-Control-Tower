from datetime import date

from .base import CloudConnector


class GcpConnector(CloudConnector):
    cloud = "gcp"
    cost_source = "Cloud Billing export no BigQuery"
    fields = [("project_id", "Projeto do BigQuery", False, "finops-billing"),
              ("billing_table", "Tabela de export", False, "finops-billing.billing.gcp_billing_export_v1_XXXXXX"),
              ("service_account_json", "Service Account (JSON)", True, "")]

    def _bq(self):
        import json
        bq = self.need("google.cloud.bigquery", "google-cloud-bigquery")
        sa = self.need("google.oauth2.service_account", "google-auth")
        cred = sa.Credentials.from_service_account_info(json.loads(self.sec["service_account_json"]))
        return bq.Client(project=self.cfg["project_id"], credentials=cred), bq

    def test(self):
        c, _ = self._bq()
        list(c.query(f"SELECT 1 FROM `{self.cfg['billing_table']}` LIMIT 1").result())
        return True, "Tabela de billing export acessível"

    def fetch_costs(self, start: date, end: date):
        c, bq = self._bq()
        sql = f"""SELECT FORMAT_DATE('%Y-%m-01', DATE(usage_start_time)) AS month, project.id AS project, service.description AS service,
                         SUM(cost) AS cost, ANY_VALUE(currency) AS currency
                  FROM `{self.cfg['billing_table']}` WHERE DATE(usage_start_time) BETWEEN @s AND @e GROUP BY 1,2,3"""
        job = c.query(sql, job_config=bq.QueryJobConfig(query_parameters=[
            bq.ScalarQueryParameter("s", "DATE", start), bq.ScalarQueryParameter("e", "DATE", end)]))
        return [{"month": date.fromisoformat(r.month), "account": r.project, "service": r.service, "cost": float(r.cost),
                 "currency": r.currency, "tags": {}} for r in job.result()]

    def fetch_recommendations(self):
        import json
        rec = self.need("google.cloud.recommender_v1", "google-cloud-recommender")
        sa = self.need("google.oauth2.service_account", "google-auth")
        cred = sa.Credentials.from_service_account_info(json.loads(self.sec["service_account_json"]))
        cl, out = rec.RecommenderClient(credentials=cred), []
        for project in self.cfg.get("projects", [self.cfg["project_id"]]):
            parent = f"projects/{project}/locations/{self.cfg.get('location', 'southamerica-east1-a')}/recommenders/google.compute.instance.MachineTypeRecommender"
            for r in cl.list_recommendations(parent=parent):
                cost = r.primary_impact.cost_projection.cost
                out.append({"account": project, "service": "Compute Engine", "resource": r.content.operation_groups[0].operations[0].resource if r.content.operation_groups else None,
                            "type": "rightsizing", "title": r.description, "savings_monthly": abs(cost.units + cost.nanos / 1e9),
                            "currency": cost.currency_code})
        return out
