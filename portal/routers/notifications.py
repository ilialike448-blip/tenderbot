from datetime import datetime

import aiosqlite
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from portal.auth import require_approved
from portal.database import get_db

router = APIRouter()


@router.get("/notifications")
async def list_notifications(
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[dict]:
    async with db.execute("""
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    """, (user["telegram_id"],)) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]


@router.get("/notifications/unread-count")
async def unread_count(
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    async with db.execute(
        "SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND is_read = 0",
        (user["telegram_id"],),
    ) as cur:
        row = await cur.fetchone()
    return {"count": dict(row)["cnt"] if row else 0}


class ReadBody(BaseModel):
    ids: list[int] = []  # empty = mark all read


@router.post("/notifications/read")
async def mark_read(
    body: ReadBody,
    user: dict = Depends(require_approved),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    if body.ids:
        placeholders = ",".join("?" * len(body.ids))
        await db.execute(
            f"UPDATE notifications SET is_read=1 WHERE user_id=? AND id IN ({placeholders})",
            [user["telegram_id"]] + body.ids,
        )
    else:
        await db.execute(
            "UPDATE notifications SET is_read=1 WHERE user_id=?",
            (user["telegram_id"],),
        )
    await db.commit()
    return {"ok": True}
