import json
from datetime import datetime
from typing import Optional

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from portal.auth import require_approved, require_lead_or_admin
from portal.database import get_db

router = APIRouter()

_REFRESH_LOCK: dict = {"last_run": 0}
REFRESH_COOLDOWN = 60  # seconds


def _fmt_tender(r) -> dict:
    d = dict(r)
    d["external_number"] = d.get("number")
    d["name"] = d.get("title")
    try:
        d["cert_requirements"] = json.loads(d.get("cert_requirements") or "[]")
    except Exception:
        d["cert_requirements"] = []
    return d


@router.get("/tenders")
async def list_tenders(
    rating: str = Query("all", regex="^(all|hot|ok|risk)$"),
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[dict]:
    rating_map = {"hot": "fire", "ok": "ok", "risk": "warn"}

    if rating == "all":
        where = ""
        params: list = []
    else:
        where = "AND (rating = ? OR rating = ?)"
        mapped = rating_map[rating]
        params = [rating, mapped]

    async with db.execute(f"""
        SELECT t.*, u.first_name AS assignee_first, u.last_name AS assignee_last,
               u.color AS assignee_color
        FROM tenders t
        LEFT JOIN users u ON t.assigned_to = u.telegram_id
        WHERE t.analyzed_at IS NOT NULL {where}
        ORDER BY
            CASE t.rating WHEN 'fire' THEN 1 WHEN 'ok' THEN 2 WHEN 'warn' THEN 3 ELSE 4 END,
            t.analyzed_at DESC
        LIMIT 50
    """, params) as cur:
        rows = await cur.fetchall()

    return [_fmt_tender(r) for r in rows]


@router.get("/tenders/{number}")
async def get_tender(
    number: str,
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    async with db.execute("""
        SELECT t.*, u.first_name AS assignee_first, u.last_name AS assignee_last,
               u.color AS assignee_color
        FROM tenders t
        LEFT JOIN users u ON t.assigned_to = u.telegram_id
        WHERE t.number = ?
    """, (number,)) as cur:
        row = await cur.fetchone()

    if not row:
        raise HTTPException(404, detail={"error": "Tender not found", "code": 404})

    d = _fmt_tender(row)

    # Attach tasks linked to this tender
    async with db.execute("""
        SELECT t.*, u.first_name AS assignee_first, u.last_name AS assignee_last
        FROM tasks t
        LEFT JOIN users u ON t.assignee_id = u.telegram_id
        WHERE t.tender_number = ?
        ORDER BY t.created_at DESC
    """, (number,)) as cur:
        task_rows = await cur.fetchall()

    d["tasks"] = [dict(r) for r in task_rows]
    return d


class TakeBody(BaseModel):
    assignee_id: Optional[int] = None  # lead/admin can assign to someone else


@router.post("/tenders/{number}/take")
async def take_tender(
    number: str,
    body: TakeBody,
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    async with db.execute(
        "SELECT * FROM tenders WHERE number = ?", (number,)
    ) as cur:
        row = await cur.fetchone()

    if not row:
        raise HTTPException(404, detail={"error": "Tender not found", "code": 404})

    t = dict(row)
    if t.get("portal_status") == "in_work":
        raise HTTPException(409, detail={"error": "Tender already taken", "code": 409})

    assignee_id = body.assignee_id if (body.assignee_id and user["role"] in ("admin", "lead")) \
        else user["telegram_id"]

    # Resolve assignee name
    async with db.execute(
        "SELECT first_name, last_name FROM users WHERE telegram_id = ?", (assignee_id,)
    ) as cur:
        arow = await cur.fetchone()
    if not arow:
        raise HTTPException(404, detail={"error": "Assignee not found", "code": 404})

    ar = dict(arow)
    assignee_name = f"{ar['first_name']} {ar.get('last_name') or ''}".strip()
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    await db.execute("""
        UPDATE tenders
        SET portal_status='in_work', assigned_to=?, taken_at=?, taken_by_name=?
        WHERE number=?
    """, (assignee_id, now, assignee_name, number))

    # Auto-create a draft task
    task_title = f"Тендер: {t['title'][:60]}"
    await db.execute("""
        INSERT INTO tasks (title, status, priority, assignee_id, tender_number, created_at)
        VALUES (?, 'new', 'high', ?, ?, ?)
    """, (task_title, assignee_id, number, now))

    await db.commit()

    async with db.execute(
        "SELECT * FROM tenders WHERE number = ?", (number,)
    ) as cur:
        updated = await cur.fetchone()

    return _fmt_tender(updated)


@router.post("/tenders/refresh")
async def refresh_tenders(
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    import time
    now = time.time()
    if now - _REFRESH_LOCK["last_run"] < REFRESH_COOLDOWN:
        remaining = int(REFRESH_COOLDOWN - (now - _REFRESH_LOCK["last_run"]))
        raise HTTPException(429, detail={"error": f"Cooldown: wait {remaining}s", "code": 429})

    _REFRESH_LOCK["last_run"] = now
    async with db.execute(
        "SELECT COUNT(*) as cnt FROM tenders WHERE analyzed_at IS NOT NULL"
    ) as cur:
        cnt_row = await cur.fetchone()

    count = dict(cnt_row)["cnt"] if cnt_row else 0
    return {"ok": True, "tenders_available": count}
