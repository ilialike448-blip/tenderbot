import io
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
_ALLOWED_IDS = os.getenv("ALLOWED_CHAT_IDS", "")
ALLOWED_CHAT_IDS = [int(x.strip()) for x in _ALLOWED_IDS.split(",") if x.strip()]

RATING_EMOJI = {"fire": "🔥", "ok": "✅", "warn": "⚠️", "bad": "❌"}


def _allowed(update: Update) -> bool:
    if not ALLOWED_CHAT_IDS:
        return True
    return update.effective_chat.id in ALLOWED_CHAT_IDS


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    await update.message.reply_text(
        "👋 TenderBot запущен!\n\n"
        "Команды:\n"
        "/tenders — последние проанализированные тендеры\n"
        "/parse — собрать новые тендеры с ЕИС\n"
        "/analyze — AI-анализ новых тендеров (Claude)\n"
        "/export — скачать Excel\n"
        "/status — статистика базы"
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    from app.database import count_tenders
    stats = count_tenders()
    await update.message.reply_text(
        f"📊 Статистика базы:\n"
        f"Всего тендеров: {stats['total']}\n"
        f"Проанализировано: {stats['analyzed']}"
    )


async def cmd_tenders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    from app.database import get_tenders

    msg = await update.message.reply_text("⏳ Загружаю тендеры…")
    tenders = get_tenders(limit=10, only_analyzed=True)

    if not tenders:
        await msg.edit_text(
            "📭 Нет проанализированных тендеров.\n"
            "Запустите /parse, затем /analyze"
        )
        return

    text = "📋 <b>Последние тендеры:</b>\n\n"
    for t in tenders[:5]:
        emoji = RATING_EMOJI.get(t.get("rating") or "", "🔲")
        nmc = f"{t['nmc']:,.0f}".replace(",", " ")
        margin = f"{t['margin_percent']:.1f}%" if t.get("margin_percent") else "—"
        title_short = t["title"][:55] + "…" if len(t["title"]) > 55 else t["title"]
        customer_short = t["customer"][:40] if t.get("customer") else "Не указан"
        text += (
            f"{emoji} <b>{title_short}</b>\n"
            f"НМЦ: {nmc} ₽ | Маржа: {margin}\n"
            f"Заказчик: {customer_short}\n"
            f'<a href="{t["url"]}">Открыть на ЕИС →</a>\n\n'
        )

    await msg.edit_text(text, parse_mode="HTML", disable_web_page_preview=True)


async def cmd_parse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    from parsers.eis_parser import parse_eis
    from app.database import save_tender

    msg = await update.message.reply_text("⏳ Шаг 1/3: Подключаюсь к ЕИС…")

    try:
        tenders = await parse_eis(pages=3)
        await msg.edit_text(f"⏳ Шаг 2/3: Сохраняю {len(tenders)} тендеров…")

        new_count = 0
        for t in tenders:
            if save_tender(t):
                new_count += 1

        await msg.edit_text(
            f"✅ Шаг 3/3: Готово!\n\n"
            f"Найдено на ЕИС: {len(tenders)}\n"
            f"Новых сохранено: {new_count}\n"
            f"Уже было в базе: {len(tenders) - new_count}\n\n"
            f"Запустите /analyze для AI-анализа"
        )
    except ConnectionError as e:
        await msg.edit_text(f"❌ Ошибка подключения к ЕИС:\n\n{e}")
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка парсинга:\n\n{e}")


async def cmd_analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    from app.database import get_unanalyzed, save_analysis
    from services.claude_agent import triage_tender, analyze_tender

    msg = await update.message.reply_text("⏳ Шаг 1/4: Загружаю тендеры для анализа…")

    tenders = get_unanalyzed(limit=20)
    if not tenders:
        await msg.edit_text("📭 Нет тендеров для анализа. Запустите /parse")
        return

    finalists = []
    for i, t in enumerate(tenders):
        await msg.edit_text(
            f"⏳ Шаг 2/4: Предфильтр (Claude Haiku)…\n"
            f"Проверено: {i}/{len(tenders)} | Прошло: {len(finalists)}"
        )
        if triage_tender(t["title"], t["nmc"]):
            finalists.append(t)

    if not finalists:
        await msg.edit_text("📭 Ни один тендер не прошёл предфильтр.")
        return

    await msg.edit_text(f"⏳ Шаг 3/4: Детальный анализ {len(finalists)} тендеров…")

    analyzed = 0
    for i, t in enumerate(finalists):
        await msg.edit_text(
            f"⏳ Шаг 3/4: Анализирую (Claude Sonnet)…\n"
            f"{i + 1}/{len(finalists)}: {t['title'][:40]}…"
        )
        try:
            result = analyze_tender(
                t["number"], t["title"], t["nmc"],
                t["customer"], t["region"],
            )
            save_analysis(result)
            analyzed += 1
        except Exception as e:
            print(f"⚠️ Анализ {t['number']} не удался: {e}", flush=True)

    await msg.edit_text(
        f"✅ Шаг 4/4: Анализ завершён!\n\n"
        f"Проверено предфильтром: {len(tenders)}\n"
        f"Прошло предфильтр: {len(finalists)}\n"
        f"Проанализировано детально: {analyzed}\n\n"
        f"Смотрите результаты: /tenders"
    )


async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _allowed(update):
        return
    from export.to_excel import generate_excel
    from datetime import datetime

    msg = await update.message.reply_text("⏳ Формирую Excel…")

    try:
        xlsx_bytes = generate_excel()
        filename = f"tenders_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        await msg.delete()
        await update.message.reply_document(
            document=io.BytesIO(xlsx_bytes),
            filename=filename,
            caption="✅ Экспорт готов",
        )
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка экспорта:\n\n{e}")


def run_bot():
    from app.database import init_db
    from parsers.scheduler import start_scheduler

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("tenders", cmd_tenders))
    app.add_handler(CommandHandler("parse", cmd_parse))
    app.add_handler(CommandHandler("analyze", cmd_analyze))
    app.add_handler(CommandHandler("export", cmd_export))

    start_scheduler()

    print("✅ Бот запущен. Жду команды…", flush=True)
    app.run_polling(poll_interval=3)
