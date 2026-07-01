import random
import time
from datetime import datetime

import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from portal.config import ADMIN_IDS, BASE_URL, BOT_TOKEN, DB_PATH

AVATAR_COLORS = [
    "#388bfd", "#3fb950", "#a78bfa", "#f0883e",
    "#f85149", "#58a6ff", "#d2a8ff",
]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def _portal_btn() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🚀 Открыть портал", web_app=WebAppInfo(url=BASE_URL))
    ]])


async def _get_or_create_user(tg_user) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA journal_mode=WAL")

        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (tg_user.id,)
        ) as cur:
            row = await cur.fetchone()

        if row:
            return dict(row)

        role = "admin" if tg_user.id in ADMIN_IDS else "member"
        status = "approved" if role == "admin" else "pending"
        color = random.choice(AVATAR_COLORS)
        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

        await db.execute(
            """INSERT INTO users
               (telegram_id, username, first_name, last_name, role, status, color, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (tg_user.id, tg_user.username, tg_user.first_name,
             tg_user.last_name, role, status, color, now),
        )
        await db.commit()
        return {"telegram_id": tg_user.id, "role": role, "status": status,
                "first_name": tg_user.first_name, "username": tg_user.username}


async def _notify_admins_new_request(user: dict) -> None:
    name = user.get("first_name", "Пользователь")
    username = f"@{user['username']}" if user.get("username") else "—"
    tid = user["telegram_id"]
    text = (
        f"📥 <b>Новая заявка на доступ</b>\n\n"
        f"👤 {name} ({username})\n"
        f"ID: <code>{tid}</code>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve:{tid}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{tid}"),
    ]])

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT telegram_id FROM users WHERE role = 'admin' AND status = 'approved'"
        ) as cur:
            admin_rows = await cur.fetchall()

    admin_tids = {r["telegram_id"] for r in admin_rows} | set(ADMIN_IDS)
    for admin_id in admin_tids:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            pass


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = await _get_or_create_user(message.from_user)
    status = user["status"]
    name = user["first_name"]

    if status == "approved":
        await message.answer(
            f"👋 Привет, {name}!\n\nНажми кнопку ниже, чтобы открыть портал.",
            reply_markup=_portal_btn(),
        )
    elif status == "pending":
        await message.answer(
            "⏳ Заявка на доступ уже отправлена.\n"
            "Ожидай подтверждения руководителя."
        )
    else:
        await message.answer("❌ В доступе отказано. Обратись к руководителю.")

    # If this was a brand new pending user — notify admins
    if status == "pending":
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT created_at FROM users WHERE telegram_id = ?", (user["telegram_id"],)
            ) as cur:
                row = await cur.fetchone()
            just_created = row and (time.time() - datetime.fromisoformat(
                dict(row)["created_at"]
            ).timestamp()) < 5

        if just_created:
            await _notify_admins_new_request(user)


@dp.message(F.text == "/whoami")
async def cmd_whoami(message: Message) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT role, status, position FROM users WHERE telegram_id = ?",
            (message.from_user.id,),
        ) as cur:
            row = await cur.fetchone()

    if not row:
        await message.answer("Тебя нет в системе. Отправь /start.")
        return

    r = dict(row)
    await message.answer(
        f"👤 Статус: <b>{r['status']}</b>\n"
        f"🎭 Роль: <b>{r['role']}</b>\n"
        f"💼 Должность: {r['position'] or '—'}",
        parse_mode="HTML",
    )


@dp.message(F.text == "/pending")
async def cmd_pending(message: Message) -> None:
    if message.from_user.id not in ADMIN_IDS:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT role FROM users WHERE telegram_id = ?", (message.from_user.id,)
            ) as cur:
                row = await cur.fetchone()
            if not row or dict(row)["role"] != "admin":
                return

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE status = 'pending' ORDER BY created_at"
        ) as cur:
            rows = await cur.fetchall()

    if not rows:
        await message.answer("📭 Нет ожидающих заявок.")
        return

    for row in rows:
        r = dict(row)
        name = r["first_name"] or "Пользователь"
        username = f"@{r['username']}" if r.get("username") else "—"
        tid = r["telegram_id"]
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve:{tid}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject:{tid}"),
        ]])
        await message.answer(
            f"👤 {name} ({username})\nID: <code>{tid}</code>",
            parse_mode="HTML", reply_markup=kb,
        )


@dp.callback_query(F.data.startswith("approve:"))
async def cb_approve(callback: CallbackQuery) -> None:
    target_id = int(callback.data.split(":")[1])
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (target_id,)
        ) as cur:
            row = await cur.fetchone()

        if not row or dict(row)["status"] == "approved":
            await callback.answer("Уже одобрен или не найден")
            return

        now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        await db.execute(
            "UPDATE users SET status='approved', approved_by=?, approved_at=? WHERE telegram_id=?",
            (callback.from_user.id, now, target_id),
        )
        await db.commit()

    try:
        await bot.send_message(
            target_id,
            "✅ Доступ открыт! Добро пожаловать в портал.",
            reply_markup=_portal_btn(),
        )
    except Exception:
        pass

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ Одобрено @{callback.from_user.username or callback.from_user.id}"
    )
    await callback.answer("Одобрено")


@dp.callback_query(F.data.startswith("reject:"))
async def cb_reject(callback: CallbackQuery) -> None:
    target_id = int(callback.data.split(":")[1])
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET status='rejected' WHERE telegram_id=?", (target_id,)
        )
        await db.commit()

    try:
        await bot.send_message(target_id, "❌ Заявка отклонена руководителем.")
    except Exception:
        pass

    await callback.message.edit_text(
        callback.message.text + f"\n\n❌ Отклонено @{callback.from_user.username or callback.from_user.id}"
    )
    await callback.answer("Отклонено")
