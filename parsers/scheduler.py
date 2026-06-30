import asyncio
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

PARSE_INTERVAL_HOURS = int(os.getenv("PARSE_INTERVAL_HOURS", "4"))


async def _run_parse_and_analyze():
    print("⏳ Планировщик: запускаю парсинг ЕИС…", flush=True)
    try:
        from parsers.eis_parser import parse_eis
        from app.database import save_tender, get_unanalyzed, save_analysis
        from services.claude_agent import triage_tender, analyze_tender

        tenders = await parse_eis(pages=5)
        new_count = sum(1 for t in tenders if save_tender(t))
        print(f"✅ Парсинг: {new_count} новых тендеров сохранено", flush=True)

        if new_count == 0:
            return

        unanalyzed = get_unanalyzed(limit=30)
        analyzed = 0
        for t in unanalyzed:
            if triage_tender(t["title"], t["nmc"]):
                try:
                    result = analyze_tender(
                        t["number"], t["title"], t["nmc"],
                        t["customer"], t["region"]
                    )
                    save_analysis(result)
                    analyzed += 1
                except Exception as e:
                    print(f"⚠️ Анализ {t['number']} не удался: {e}", flush=True)

        print(f"✅ Анализ: {analyzed} тендеров обработано", flush=True)

    except ConnectionError as e:
        print(f"❌ Планировщик: ошибка ЕИС — {e}", flush=True)
    except Exception as e:
        print(f"❌ Планировщик: неожиданная ошибка — {e}", flush=True)


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _run_parse_and_analyze,
        trigger=IntervalTrigger(hours=PARSE_INTERVAL_HOURS),
        id="parse_and_analyze",
        name=f"Парсинг ЕИС каждые {PARSE_INTERVAL_HOURS}ч",
        replace_existing=True,
    )
    scheduler.start()
    print(f"✅ Планировщик запущен (каждые {PARSE_INTERVAL_HOURS} ч)", flush=True)
    return scheduler
