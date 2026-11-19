"""Contrato dos conectores multi-cloud. Cada conector devolve registros NORMALIZADOS:
  custo:  {"month": date, "account": str, "service": str, "cost": float, "currency": str, "tags": dict}
  recurso: {"account": str, "service": str, "type": str, "name": str, "region": str, "tags": dict, "monthly_cost": float|None}
  recomendacao: {"account": str, "service": str, "resource": str|None, "type": str, "title": str, "savings_monthly": float, "currency": str}
Os SDKs sao importados sob demanda (pip install -r requirements-connectors.txt).
"""
from __future__ import annotations

from datetime import date


class ConnectorUnavailable(RuntimeError):
    pass


class CloudConnector:
    cloud = ""
    cost_source = ""
    # campos exibidos no formulario: (chave, rotulo, secreto?, exemplo)
    fields: list[tuple[str, str, bool, str]] = []

    def __init__(self, config: dict, secrets: dict):
        self.cfg, self.sec = config, secrets

    def test(self) -> tuple[bool, str]:
        raise NotImplementedError

    def fetch_costs(self, start: date, end: date) -> list[dict]:
        raise NotImplementedError

    def fetch_resources(self) -> list[dict]:
        return []

    def fetch_recommendations(self) -> list[dict]:
        return []

    @staticmethod
    def need(module: str, pkg: str):
        try:
            return __import__(module, fromlist=["x"])
        except ImportError as e:
            raise ConnectorUnavailable(f"SDK ausente ({pkg}). Rode: pip install -r requirements-connectors.txt") from e
