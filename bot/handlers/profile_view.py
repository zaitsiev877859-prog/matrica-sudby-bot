"""МН-05 «Профиль». Только просмотр; редактирование (ЭК-44) - следующий этап."""

from aiogram import F, Router
from aiogram.types import Message

from bot.db import repo
from bot.db.pool import get_pool

router = Router(name="profile_view")


@router.message(F.text == "Профиль")
async def show_profile(message: Message) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        specialist = await repo.get_specialist_by_telegram_id(conn, message.from_user.id)

    if specialist is None:
        await message.answer("Сначала пройди /start.")
        return

    lines = [
        f"Имя: {specialist['display_name']}",
        f"Псевдоним: {specialist['alias'] or '-'}",
        f"Контакт: {specialist['contact_value'] or '-'}",
        f"Язык: {specialist['language']}",
        "",
        "Изменение профиля через бота (ЭК-44) - в разработке.",
    ]
    await message.answer("\n".join(lines))
