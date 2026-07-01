import aiosqlite
from fastapi import APIRouter, Depends, Query

from portal.auth import require_approved
from portal.database import get_db

router = APIRouter()

PERIOD_DAYS = {"week": 7, "month": 30, "quarter": 90}


@router.get("/analytics")
async def get_analytics(
    period: str = Query("week", regex="^(week|month|quarter)$"),
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    days = PERIOD_DAYS[period]
    since = f"-{days} days"

    async with db.execute("""
        SELECT
            COUNT(*) as tenders_taken,
            SUM(nmc) as total_sum,
            SUM(cost_estimate) as total_cost,
            COUNT(CASE WHEN analyzed_at IS NOT NULL THEN 1 END) as ai_found
        FROM tenders
        WHERE portal_status IN ('in_work','submitted','won') AND taken_at >= datetime('now', ?)
    """, (since,)) as cur:
        row = await cur.fetchone()

    agg = dict(row) if row else {}
    total_sum = agg.get("total_sum") or 0
    total_cost = agg.get("total_cost") or 0
    profit = total_sum - total_cost if total_sum and total_cost else None
    margin = round((profit / total_sum * 100), 1) if profit and total_sum else None

    # Per-tender breakdown
    async with db.execute("""
        SELECT t.external_number, t.name, t.nmc, t.cost_estimate, t.margin_percent,
               t.rating, t.analyzed_at, t.taken_at, t.delivery_deadline,
               u.first_name, u.last_name
        FROM tenders t
        LEFT JOIN users u ON t.assigned_to = u.telegram_id
        WHERE t.portal_status IN ('in_work','submitted','won')
          AND t.taken_at >= datetime('now', ?)
        ORDER BY t.taken_at DESC
    """, (since,)) as cur:
        tender_rows = await cur.fetchall()

    per_tender = []
    for r in tender_rows:
        rd = dict(r)
        nmc = rd.get("nmc") or 0
        cost = rd.get("cost_estimate") or 0
        ten_profit = (nmc - cost) if nmc and cost else None
        rd["profit"] = ten_profit
        rd["assignee_name"] = f"{rd.get('first_name') or ''} {rd.get('last_name') or ''}".strip() or None
        per_tender.append(rd)

    # AI found total (ever analyzed)
    async with db.execute(
        "SELECT COUNT(*) as cnt FROM tenders WHERE analyzed_at IS NOT NULL"
    ) as cur:
        ai_row = await cur.fetchone()
    ai_found_total = dict(ai_row)["cnt"] if ai_row else 0

    return {
        "period": period,
        "summary": {
            "tenders_taken": agg.get("tenders_taken") or 0,
            "ai_found": ai_found_total,
            "total_sum": total_sum,
            "total_cost": total_cost,
            "profit_forecast": profit,
            "margin_pct": margin,
        },
        "per_tender": per_tender,
    }
