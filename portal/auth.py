import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl, unquote

import aiosqlite
from fastapi import Depends, Header, HTTPException

from portal.config import BOT_TOKEN
from portal.database import get_db


def validate_init_data(init_data: str) -> dict:
    """HMAC-SHA256 validation per Telegram docs. Raises ValueError on failure."""
    vals = dict(parse_qsl(init_data, strict_parsing=True))
    hash_str = vals.pop("hash", None)
    if not hash_str:
        raise ValueError("no hash in initData")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(vals.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    computed = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed, hash_str):
        raise ValueError("initData signature mismatch")

    auth_date = int(vals.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        raise ValueError("initData expired (>24h)")

    return vals


async def get_current_user(
    authorization: str = Header(...),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    if not authorization.startswith("tma "):
        raise HTTPException(401, detail={"error": "Invalid auth format", "code": 401})

    init_data = authorization[4:]
    try:
        vals = validate_init_data(init_data)
    except ValueError as exc:
        raise HTTPException(401, detail={"error": str(exc), "code": 401})

    raw_user = vals.get("user", "{}")
    user_data = json.loads(unquote(raw_user))
    telegram_id = user_data.get("id")
    if not telegram_id:
        raise HTTPException(401, detail={"error": "No user in initData", "code": 401})

    async with db.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    ) as cur:
        row = await cur.fetchone()

    if not row:
        raise HTTPException(401, detail={"error": "User not registered. Send /start to bot.", "code": 401})

    await db.execute(
        "UPDATE users SET last_seen = ? WHERE telegram_id = ?",
        (time.strftime("%Y-%m-%dT%H:%M:%S"), telegram_id),
    )
    await db.commit()

    return dict(row)


async def require_approved(user: dict = Depends(get_current_user)) -> dict:
    if user["status"] != "approved":
        raise HTTPException(403, detail={"error": f"Access denied: {user['status']}", "code": 403})
    return user


async def require_admin(user: dict = Depends(require_approved)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(403, detail={"error": "Admin access required", "code": 403})
    return user


async def require_lead_or_admin(user: dict = Depends(require_approved)) -> dict:
    if user["role"] not in ("admin", "lead"):
        raise HTTPException(403, detail={"error": "Lead or admin access required", "code": 403})
    return user
