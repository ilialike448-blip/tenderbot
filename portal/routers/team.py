import aiosqlite
from fastapi import APIRouter, Depends, Query

from portal.auth import require_approved
from portal.database import get_db

router = APIRouter()

PERIOD_DAYS = {"week": 7, "month": 30, "quarter": 90}


@router.get("/team")
async def get_team(
    period: str = Query("week", regex="^(week|month|quarter)$"),
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    days = PERIOD_DAYS[period]

    async with db.execute(f"""
        SELECT u.telegram_id, u.first_name, u.last_name, u.username,
               u.role, u.position, u.color, u.last_seen,
               (SELECT COUNT(*) FROM tasks t WHERE t.assignee_id=u.telegram_id
                  AND t.status='done'
                  AND t.closed_at >= datetime('now', '-{days} days')) as done,
               (SELECT COUNT(*) FROM tasks t WHERE t.assignee_id=u.telegram_id
                  AND t.status='in_work') as in_work,
               (SELECT COUNT(*) FROM tasks t WHERE t.assignee_id=u.telegram_id
                  AND t.status='new') as new_count,
               (SELECT COUNT(*) FROM tenders ten WHERE ten.assigned_to=u.telegram_id
                  AND ten.taken_at >= datetime('now', '-{days} days')) as tenders_count,
               (SELECT number FROM tenders WHERE assigned_to=u.telegram_id
                  AND portal_status='in_work' LIMIT 1) as active_tender_num,
               (SELECT title FROM tenders WHERE assigned_to=u.telegram_id
                  AND portal_status='in_work' LIMIT 1) as active_tender_name
        FROM users u
        WHERE u.status='approved'
        ORDER BY tenders_count DESC, done DESC
    """) as cur:
        rows = await cur.fetchall()

    members = []
    for r in rows:
        rd = dict(r)
        rd["initials"] = _initials(rd.get("first_name"), rd.get("last_name"))
        rd["is_active"] = _is_active(rd.get("last_seen"))
        members.append(rd)

    # Top 3 by tenders taken this period
    top3 = sorted(members, key=lambda m: m.get("tenders_count", 0), reverse=True)[:3]

    return {"members": members, "top3": top3}


@router.get("/employees/{telegram_id}")
async def get_employee(
    telegram_id: int,
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    async with db.execute(
        "SELECT * FROM users WHERE telegram_id = ? AND status = 'approved'",
        (telegram_id,),
    ) as cur:
        row = await cur.fetchone()

    if not row:
        from fastapi import HTTPException
        raise HTTPException(404, detail={"error": "Employee not found", "code": 404})

    emp = dict(row)
    emp["initials"] = _initials(emp.get("first_name"), emp.get("last_name"))

    async with db.execute("""
        SELECT t.*, ten.title AS tender_name
        FROM tasks t
        LEFT JOIN tenders ten ON t.tender_number = ten.number
        WHERE t.assignee_id = ?
        ORDER BY t.created_at DESC
        LIMIT 20
    """, (telegram_id,)) as cur:
        task_rows = await cur.fetchall()

    emp["tasks"] = [dict(r) for r in task_rows]

    async with db.execute("""
        SELECT * FROM tenders
        WHERE assigned_to = ?
        ORDER BY taken_at DESC
        LIMIT 10
    """, (telegram_id,)) as cur:
        tender_rows = await cur.fetchall()

    emp["tenders"] = [dict(r) for r in tender_rows]
    return emp


def _initials(first: str | None, last: str | None) -> str:
    parts = []
    if first:
        parts.append(first[0].upper())
    if last:
        parts.append(last[0].upper())
    return "".join(parts) or "?"


def _is_active(last_seen: str | None) -> bool:
    if not last_seen:
        return False
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(last_seen)
        return (datetime.utcnow() - dt).total_seconds() < 300
    except Exception:
        return False
