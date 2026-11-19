from fastapi import APIRouter, Query
from ..services import kpis as K
from ..services.common import month_range, parse_month

router = APIRouter(prefix="/api/executive", tags=["executivo"])


@router.get("/overview")
def overview(month: str | None = None):
    m = parse_month(month)
    ct = K.company_table(m)
    return {
        "month": m.isoformat(),
        "kpis": K.kpi_block(m),
        "trend": K.trend(),
        "by_company": ct,
        "by_cloud": K.cloud_table(m),
        "savings": K.savings_series(),
        "top_consumers": K.top_consumers(m, "application", 20),
        "budget_vs_actual": [{"code": c["code"], "name": c["name"], "actual": c["cost"], "budget": c["budget"],
                              "variance_pct": c["variance_pct"]} for c in ct],
    }


@router.get("/top-consumers")
def top(month: str | None = None, dimension: str = Query("application", pattern="^(application|resource|account)$"),
        limit: int = Query(20, ge=1, le=100), company: str | None = None):
    return K.top_consumers(parse_month(month), dimension, limit, company)
