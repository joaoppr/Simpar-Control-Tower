from fastapi import APIRouter
from ..db import q
from ..services.common import add_months, month_range, org_id, reference_month

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/meta")
def meta():
    ref = reference_month()
    return {
        "org": q("SELECT code, name FROM org WHERE id=:o", o=org_id())[0],
        "demo_mode": True,
        "reference_month": ref.isoformat(),
        "months": [m.isoformat() for m in month_range()],
        "forecast_months": [add_months(ref, i).isoformat() for i in (1, 2, 3)],
        "companies": q("SELECT code, name, segment, color FROM dim_company WHERE org_id=:o ORDER BY id", o=org_id()),
        "clouds": q("SELECT code, name, color, cost_source FROM dim_cloud ORDER BY code"),
    }
