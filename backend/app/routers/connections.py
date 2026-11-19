import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..connectors.base import ConnectorUnavailable
from ..connectors.factory import CONNECTORS, get_connector, provider_specs
from ..db import execute, insert_returning, q, q1
from ..etl.pipeline import sync_connection
from ..security import decrypt, encrypt
from ..services.common import org_id

router = APIRouter(prefix="/api/connections", tags=["conexoes"])


class ConnectionIn(BaseModel):
    company: str
    cloud: str
    display_name: str
    mode: str = "demo"
    config: dict = {}
    secrets: dict = {}


def _row(i: int) -> dict:
    r = q1("""SELECT cc.*, co.code AS company_code, co.name AS company_name FROM cloud_connection cc
              JOIN dim_company co ON co.id=cc.company_id WHERE cc.id=:i AND co.org_id=:o""", i=i, o=org_id())
    if not r:
        raise HTTPException(404, "Conexão não encontrada")
    return r


@router.get("/providers")
def providers():
    return provider_specs()


@router.get("")
def listing():
    rows = q("""SELECT cc.id, cc.company_id, co.code AS company_code, co.name AS company_name, cc.cloud_code, cl.name AS cloud_name,
                       cc.display_name, cc.auth_type, cc.config, cc.mode, cc.status, cc.sync_enabled, cc.last_sync_at, cc.last_message,
                       (cc.secret_enc IS NOT NULL) AS has_secret, cl.cost_source
                FROM cloud_connection cc JOIN dim_company co ON co.id=cc.company_id JOIN dim_cloud cl ON cl.code=cc.cloud_code
                WHERE co.org_id=:o ORDER BY co.id, cc.cloud_code""", o=org_id())
    return rows


@router.post("")
def create(body: ConnectionIn):
    if body.cloud not in CONNECTORS:
        raise HTTPException(422, "Cloud inválida")
    if body.mode not in ("demo", "live"):
        raise HTTPException(422, "Modo inválido")
    co = q1("SELECT id FROM dim_company WHERE org_id=:o AND code=:c", o=org_id(), c=body.company)
    if not co:
        raise HTTPException(404, "Empresa não encontrada")
    new_id = insert_returning(
        """INSERT INTO cloud_connection (company_id, cloud_code, display_name, auth_type, config, secret_enc, mode, status)
           VALUES (:c,:cl,:n,:a,CAST(:cfg AS jsonb),:s,:m,'pending') RETURNING id""",
        c=co["id"], cl=body.cloud, n=body.display_name, a=CONNECTORS[body.cloud].cost_source,
        cfg=json.dumps(body.config), s=encrypt(body.secrets) if body.secrets else None, m=body.mode)
    return {"id": new_id}


@router.post("/{cid}/test")
def test(cid: int):
    r = _row(cid)
    if r["mode"] == "demo":
        ok, msg = r["status"] != "error", "Modo demonstração: conexão simulada" if r["status"] != "error" else "Credencial expirada (simulado)"
    else:
        try:
            ok, msg = get_connector(r["cloud_code"], r["config"], decrypt(r["secret_enc"])).test()
        except ConnectorUnavailable as e:
            ok, msg = False, str(e)
        except Exception as e:
            ok, msg = False, f"Falha na conexão: {str(e)[:200]}"
    execute("UPDATE cloud_connection SET status=:s, last_message=:m WHERE id=:i", s="connected" if ok else "error", m=msg, i=cid)
    return {"ok": ok, "message": msg}


@router.post("/{cid}/sync")
def sync(cid: int):
    _row(cid)
    return sync_connection(cid)


@router.patch("/{cid}")
def toggle(cid: int, sync_enabled: bool):
    _row(cid)
    execute("UPDATE cloud_connection SET sync_enabled=:s WHERE id=:i", s=sync_enabled, i=cid)
    return {"ok": True}


@router.delete("/{cid}")
def delete(cid: int):
    _row(cid)
    execute("DELETE FROM cloud_connection WHERE id=:i", i=cid)
    return {"ok": True}


@router.get("/runs/recent")
def runs():
    return q("""SELECT e.id, e.connection_id, cc.display_name, e.started_at, e.finished_at, e.status, e.rows_cost, e.rows_resources, e.rows_recs, e.message
                FROM etl_run e JOIN cloud_connection cc ON cc.id=e.connection_id JOIN dim_company co ON co.id=cc.company_id
                WHERE co.org_id=:o ORDER BY e.started_at DESC LIMIT 30""", o=org_id())
