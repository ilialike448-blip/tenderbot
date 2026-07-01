import aiosqlite
from fastapi import APIRouter, Depends, Query

from portal.auth import require_approved
from portal.database import get_db

router = APIRouter()

PERIOD_DAYS = {"week": 7, "month": 30, "quarter": 90}


@router.get("/dashboard")
async def get_dashboard(
    period: str = Query("week", regex="^(week|month|quarter)$"),
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    days = PERIOD_DAYS[period]

    # Task summary
    async with db.execute("""
        SELECT
            SUM(CASE WHEN status='done'    THEN 1 ELSE 0 END) as done,
            SUM(CASE WHEN status='in_work' THEN 1 ELSE 0 END) as in_work,
            SUM(CASE WHEN status='new'     THEN 1 ELSE 0 END) as new_count
        FROM tasks
        WHERE created_at >= datetime('now', ?)
    """, (f"-{days} days",)) as cur:
        stats = dict(await cur.fetchone() or {})

    # Team list with their task counts
    async with db.execute("""
        SELECT u.telegram_id, u.first_name, u.last_name, u.username,
               u.role, u.position, u.color, u.last_seen,
               (SELECT COUNT(*) FROM tasks t WHERE t.assignee_id=u.telegram_id AND t.status='done'
                  AND t.closed_at >= datetime('now', ?)) as done,
               (SELECT COUNT(*) FROM tasks t WHERE t.assignee_id=u.telegram_id AND t.status='in_work') as in_work,
               (SELECT COUNT(*) FROM tasks t WHERE t.assignee_id=u.telegram_id AND t.status='new') as new_count,
               (SELECT external_number FROM tenders WHERE assigned_to=u.telegram_id
                  AND portal_status='in_work' LIMIT 1) as active_tender_num,
               (SELECT name FROM tenders WHERE assigned_to=u.telegram_id
                  AND portal_status='in_work' LIMIT 1) as active_tender_name
        FROM users u
        WHERE u.status='approved'
        ORDER BY u.first_name
    """, (f"-{days} days",)) as cur:
        team_rows = await cur.fetchall()

    team = []
    for r in team_rows:
        rd = dict(r)
        rd["initials"] = _initials(rd.get("first_name"), rd.get("last_name"))
        rd["is_active"] = _is_active(rd.get("last_seen"))
        team.append(rd)

    # Processes (recent tasks)
    async with db.execute("""
        SELECT t.id, t.title, t.status, t.due_date,
               u.first_name, u.last_name
        FROM tasks t
        LEFT JOIN users u ON t.assignee_id = u.telegram_id
        WHERE t.status != 'done'
        ORDER BY t.created_at DESC
        LIMIT 5
    """) as cur:
        proc_rows = await cur.fetchall()

    processes = [dict(r) for r in proc_rows]

    # Tenders in work
    async with db.execute("""
        SELECT external_number, name, assigned_to, taken_at, nmc, end_date,
               taken_by_name
        FROM tenders
        WHERE portal_status = 'in_work'
        ORDER BY taken_at DESC
        LIMIT 5
    """) as cur:
        wip_rows = await cur.fetchall()

    tenders_in_work = [dict(r) for r in wip_rows]

    return {
        "summary": {
            "done": stats.get("done") or 0,
            "in_work": stats.get("in_work") or 0,
            "new": stats.get("new_count") or 0,
        },
        "team": team,
        "processes": processes,
        "tenders_in_work": tenders_in_work,
    }


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
