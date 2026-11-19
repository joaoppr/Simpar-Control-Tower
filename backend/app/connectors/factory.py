from .aws import AwsConnector
from .azure import AzureConnector
from .base import CloudConnector
from .gcp import GcpConnector
from .huawei import HuaweiConnector
from .oci import OciConnector

CONNECTORS: dict[str, type[CloudConnector]] = {c.cloud: c for c in (AwsConnector, AzureConnector, OciConnector, GcpConnector, HuaweiConnector)}


def get_connector(cloud: str, config: dict, secrets: dict) -> CloudConnector:
    return CONNECTORS[cloud](config, secrets)


def provider_specs() -> list[dict]:
    return [{"cloud": k, "cost_source": c.cost_source,
             "fields": [{"key": f[0], "label": f[1], "secret": f[2], "placeholder": f[3]} for f in c.fields]} for k, c in CONNECTORS.items()]
