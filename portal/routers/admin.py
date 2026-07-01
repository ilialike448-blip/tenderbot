from datetime import datetime

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from portal.auth import require_admin
from portal.database import get_db

router = APIRouter(prefix="/admin")


def _user_row(row) -> dict:
    r = dict(row)
    parts = []
    if r.get("first_name"):
        parts.append(r["first_name"][0].upper())
    if r.get("last_name"):
        parts.append(r["last_name"][0].upper())
    r["initials"] = "".join(parts) or "?"
    return r


@router.get("/users")
async def list_users(
    _admin: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[dict]:
    async with db.execute(
        "SELECT * FROM users ORDER BY created_at DESC"
    ) as cur:
        rows = await cur.fetchall()
    return [_user_row(r) for r in rows]


@router.get("/pending")
async def list_pending(
    _admin: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[dict]:
    async with db.execute(
        "SELECT * FROM users WHERE status = 'pending' ORDER BY created_at"
    ) as cur:
        rows = await cur.fetchall()
    return [_user_row(r) for r in rows]


@router.post("/users/{telegram_id}/approve")
async def approve_user(
    telegram_id: int,
    admin: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    await db.execute(
        "UPDATE users SET status='approved', approved_by=?, approved_at=? WHERE telegram_id=?",
        (admin["telegram_id"], now, telegram_id),
    )
    await db.commit()

    # Send bot notification
    try:
        from portal.bot import bot, _portal_btn
        await bot.send_message(telegram_id, "✅ Доступ открыт!", reply_markup=_portal_btn())
    except Exception:
        pass

    return {"ok": True}


@router.post("/users/{telegram_id}/reject")
async def reject_user(
    telegram_id: int,
    _admin: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    await db.execute(
        "UPDATE users SET status='rejected' WHERE telegram_id=?", (telegram_id,)
    )
    await db.commit()
    try:
        from portal.bot import bot
        await bot.send_message(telegram_id, "❌ Заявка на доступ отклонена.")
    except Exception:
        pass
    return {"ok": True}


@router.post("/users/{telegram_id}/block")
async def block_user(
    telegram_id: int,
    _admin: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    await db.execute(
        "UPDATE users SET status='blocked' WHERE telegram_id=?", (telegram_id,)
    )
    await db.commit()
    return {"ok": True}


class RoleUpdate(BaseModel):
    role: str  # admin / lead / member


@router.patch("/users/{telegram_id}/role")
async def update_role(
    telegram_id: int,
    body: RoleUpdate,
    _admin: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    if body.role not in ("admin", "lead", "member"):
        raise HTTPException(400, detail={"error": "Invalid role", "code": 400})
    await db.execute(
        "UPDATE users SET role=? WHERE telegram_id=?", (body.role, telegram_id)
    )
    await db.commit()
    return {"ok": True}
