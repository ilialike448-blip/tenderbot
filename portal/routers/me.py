import time

import aiosqlite
from fastapi import APIRouter, Depends

from portal.auth import get_current_user, require_approved
from portal.database import get_db

router = APIRouter()


@router.get("/me")
async def get_me(
    user: dict = Depends(get_current_user),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    """Returns current user profile. Accessible to pending users (so frontend knows to show gate)."""
    initials = _initials(user.get("first_name"), user.get("last_name"))
    return {
        "telegram_id": user["telegram_id"],
        "first_name": user["first_name"],
        "last_name": user.get("last_name"),
        "username": user.get("username"),
        "role": user["role"],
        "status": user["status"],
        "position": user.get("position"),
        "color": user.get("color", "#388bfd"),
        "initials": initials,
    }


def _initials(first: str | None, last: str | None) -> str:
    parts = []
    if first:
        parts.append(first[0].upper())
    if last:
        parts.append(last[0].upper())
    return "".join(parts) or "?"
