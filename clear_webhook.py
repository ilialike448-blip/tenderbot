import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

async def main():
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        print("❌ BOT_TOKEN не найден в .env")
        return
    bot = Bot(token)
    await bot.delete_webhook(drop_pending_updates=True)
    info = await bot.get_me()
    print(f"✅ Вебхук очищен. Бот: @{info.username}")

asyncio.run(main())
