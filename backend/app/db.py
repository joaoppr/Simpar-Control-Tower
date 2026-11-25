from typing import Any
from sqlalchemy import create_engine, text
from .config import settings

database_url = settings.database_url
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(database_url, pool_pre_ping=True, pool_size=8, max_overflow=8, future=True)


def q(sql: str, **params: Any) -> list[dict]:
    """Executa SQL parametrizado e devolve lista de dicts (numericos Decimal -> float)."""
    with engine.connect() as c:
        rows = c.execute(text(sql), params).mappings().all()
    return [_clean(dict(r)) for r in rows]


def q1(sql: str, **params: Any) -> dict:
    r = q(sql, **params)
    return r[0] if r else {}


def scalar(sql: str, **params: Any):
    with engine.connect() as c:
        v = c.execute(text(sql), params).scalar()
    return _num(v)


def execute(sql: str, **params: Any) -> None:
    with engine.begin() as c:
        c.execute(text(sql), params)


def _num(v):
    from decimal import Decimal
    return float(v) if isinstance(v, Decimal) else v


def _clean(d: dict) -> dict:
    return {k: _num(v) for k, v in d.items()}


def insert_returning(sql: str, **params: Any) -> Any:
    with engine.begin() as c:
        return _num(c.execute(text(sql), params).scalar())
