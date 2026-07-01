import os

BOT_TOKEN: str = os.getenv("PORTAL_BOT_TOKEN", "")
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",") if x.strip()
]
DB_PATH: str = os.getenv("DB_PATH", "./tenderbot.db")
BASE_URL: str = os.getenv("PORTAL_BASE_URL", "")        # https://xxx.trycloudflare.com
WEBHOOK_SECRET: str = os.getenv("PORTAL_WEBHOOK_SECRET", "changeme")
PORT: int = int(os.getenv("PORTAL_PORT", "8000"))
