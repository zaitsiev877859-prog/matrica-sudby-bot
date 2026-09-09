import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN, DATABASE_URL
from bot.db.pool import close_pool, init_pool
from bot.handlers import profile, profile_view, report_demo, rights, stub_sections, support


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    await init_pool(DATABASE_URL)

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.include_router(profile.router)
    dp.include_router(profile_view.router)
    dp.include_router(report_demo.router)
    dp.include_router(rights.router)
    dp.include_router(support.router)
    dp.include_router(stub_sections.router)

    try:
        await dp.start_polling(bot)
    finally:
        await close_pool()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
