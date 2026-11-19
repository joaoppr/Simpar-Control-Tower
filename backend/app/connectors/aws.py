from datetime import date

from .base import CloudConnector


class AwsConnector(CloudConnector):
    cloud = "aws"
    cost_source = "AWS Cost Explorer (fonte primária)"
    fields = [("access_key_id", "Access Key ID", False, "AKIA..."), ("secret_access_key", "Secret Access Key", True, ""),
              ("role_arn", "Role ARN (AssumeRole, opcional)", False, "arn:aws:iam::123456789012:role/finops-readonly"),
              ("tag_key", "Tag de alocação (opcional)", False, "product")]

    def _session(self):
        boto3 = self.need("boto3", "boto3")
        s = boto3.Session(aws_access_key_id=self.sec.get("secret_access_key") and self.cfg.get("access_key_id"),
                          aws_secret_access_key=self.sec.get("secret_access_key"), region_name="us-east-1")
        if self.cfg.get("role_arn"):
            c = s.client("sts").assume_role(RoleArn=self.cfg["role_arn"], RoleSessionName="simpar-finops")["Credentials"]
            s = boto3.Session(aws_access_key_id=c["AccessKeyId"], aws_secret_access_key=c["SecretAccessKey"],
                              aws_session_token=c["SessionToken"], region_name="us-east-1")
        return s

    def test(self):
        s = self._session()
        ident = s.client("sts").get_caller_identity()
        s.client("ce").get_cost_and_usage(TimePeriod={"Start": date.today().replace(day=1).isoformat(),
                                                      "End": date.today().isoformat() if date.today().day > 1 else
                                                      date.today().replace(day=2).isoformat()},
                                          Granularity="DAILY", Metrics=["UnblendedCost"])
        return True, f"Conectado como {ident['Arn']} · Cost Explorer acessível"

    def fetch_costs(self, start: date, end: date):
        ce, out, token = self._session().client("ce"), [], None
        group = [{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}, {"Type": "DIMENSION", "Key": "SERVICE"}]
        if self.cfg.get("tag_key"):
            group = group[:1] + [{"Type": "TAG", "Key": self.cfg["tag_key"]}]
        while True:
            kw = dict(TimePeriod={"Start": start.isoformat(), "End": end.isoformat()}, Granularity="MONTHLY",
                      Metrics=["UnblendedCost"], GroupBy=group)
            if token:
                kw["NextPageToken"] = token
            r = ce.get_cost_and_usage(**kw)
            for p in r["ResultsByTime"]:
                for g in p["Groups"]:
                    k = g["Keys"]
                    tags = {self.cfg["tag_key"]: k[1].split("$", 1)[-1]} if self.cfg.get("tag_key") else {}
                    out.append({"month": date.fromisoformat(p["TimePeriod"]["Start"]), "account": k[0],
                                "service": k[1] if not tags else "Tag:" + k[1],
                                "cost": float(g["Metrics"]["UnblendedCost"]["Amount"]),
                                "currency": g["Metrics"]["UnblendedCost"]["Unit"], "tags": tags})
            token = r.get("NextPageToken")
            if not token:
                return out

    def fetch_resources(self):
        s, out = self._session(), []
        for page in s.client("resourcegroupstaggingapi").get_paginator("get_resources").paginate():
            for m in page["ResourceTagMappingList"]:
                arn = m["ResourceARN"].split(":")
                out.append({"account": arn[4], "service": arn[2], "type": arn[5].split("/")[0] if len(arn) > 5 else "",
                            "name": m["ResourceARN"].split("/")[-1], "region": arn[3],
                            "tags": {t["Key"]: t["Value"] for t in m["Tags"]}, "monthly_cost": None})
        return out

    def fetch_recommendations(self):
        ce, out = self._session().client("ce"), []
        r = ce.get_rightsizing_recommendation(Service="AmazonEC2", Configuration={"RecommendationTarget": "SAME_INSTANCE_FAMILY",
                                                                                   "BenefitsConsidered": True})
        for x in r.get("RightsizingRecommendations", []):
            det = x.get("ModifyRecommendationDetail", {}).get("TargetInstances", [{}])[0]
            out.append({"account": x["AccountId"], "service": "EC2", "resource": x["CurrentInstance"]["ResourceId"],
                        "type": "rightsizing" if x["RightsizingType"] == "MODIFY" else "idle_resources",
                        "title": f"{x['RightsizingType']} {x['CurrentInstance']['ResourceId']}",
                        "savings_monthly": float(det.get("EstimatedMonthlySavings", x.get("TerminateRecommendationDetail", {}).get("EstimatedMonthlySavings", 0))),
                        "currency": "USD"})
        sp = ce.get_savings_plans_purchase_recommendation(SavingsPlansType="COMPUTE_SP", TermInYears="ONE_YEAR",
                                                          PaymentOption="NO_UPFRONT", LookbackPeriodInDays="THIRTY_DAYS")
        s = sp.get("SavingsPlansPurchaseRecommendation", {}).get("SavingsPlansPurchaseRecommendationSummary", {})
        if s:
            out.append({"account": "payer", "service": "Savings Plans", "resource": None, "type": "savings_plans",
                        "title": "Compromisso de Compute Savings Plan recomendado",
                        "savings_monthly": float(s.get("EstimatedMonthlySavingsAmount", 0)), "currency": "USD"})
        return out
