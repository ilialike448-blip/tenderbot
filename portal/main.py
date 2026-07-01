from contextlib import asynccontextmanager
from pathlib import Path

from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import portal.config as cfg
from portal.bot import bot, dp
from portal.database import init_portal_schema
from portal.routers import admin, analytics, dashboard, me, notifications, tasks, tenders, team


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_portal_schema()

    if cfg.BOT_TOKEN and cfg.BASE_URL and cfg.WEBHOOK_SECRET:
        webhook_url = f"{cfg.BASE_URL}/tg/webhook"
        for attempt in range(3):
            try:
                await bot.set_webhook(
                    url=webhook_url,
                    secret_token=cfg.WEBHOOK_SECRET,
                    drop_pending_updates=True,
                )
                print(f"✅ Webhook set: {webhook_url}", flush=True)
                break
            except Exception as e:
                print(f"⚠️  Webhook attempt {attempt+1}/3 failed: {e}", flush=True)
                if attempt < 2:
                    import asyncio
                    await asyncio.sleep(3)
        else:
            print("⚠️  Webhook not set after 3 attempts — bot commands unavailable", flush=True)
    else:
        print("⚠️  Webhook not set — PORTAL_BOT_TOKEN / PORTAL_BASE_URL / PORTAL_WEBHOOK_SECRET missing", flush=True)

    yield

    if cfg.BOT_TOKEN:
        await bot.delete_webhook()
        await bot.session.close()


app = FastAPI(lifespan=lifespan, title="TenderPortal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": str(exc), "code": 500})


# Telegram webhook
@app.post("/tg/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None),
) -> dict:
    if x_telegram_bot_api_secret_token != cfg.WEBHOOK_SECRET:
        raise HTTPException(403, detail="Invalid secret token")
    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return {"ok": True}


# API routes
api_prefix = "/api"
app.include_router(me.router,            prefix=api_prefix)
app.include_router(admin.router,         prefix=api_prefix)
app.include_router(dashboard.router,     prefix=api_prefix)
app.include_router(tasks.router,         prefix=api_prefix)
app.include_router(tenders.router,       prefix=api_prefix)
app.include_router(team.router,          prefix=api_prefix)
app.include_router(analytics.router,     prefix=api_prefix)
app.include_router(notifications.router, prefix=api_prefix)

# Serve built Mini App static files
_static_dir = Path(__file__).parent.parent / "miniapp" / "dist"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="miniapp")
else:
    @app.get("/")
    async def index():
        return {"message": "Mini App not built yet. Run: cd miniapp && npm run build"}
