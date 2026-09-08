"""МН-03 «Мои права». Чтение агрегатов ДН-07 (см. 04c, раздел 7 и ПР-03)."""

from aiogram import F, Router
from aiogram.types import Message

from bot.db import repo
from bot.db.pool import get_pool

router = Router(name="rights")

RIGHT_LABELS = {
    "demo": "Демо",
    "single": "Разовое право",
    "pack10": "Пакет 10 отчётов",
    "unlimited30": "Безлимит 30 дней",
}


@router.message(F.text == "Мои права")
async def show_rights(message: Message) -> None:
    pool = get_pool()
    async with pool.acquire() as conn:
        specialist = await repo.get_specialist_by_telegram_id(conn, message.from_user.id)
        if specialist is None:
            await message.answer("Сначала пройди /start.")
            return
        rows = await repo.get_rights_summary(conn, specialist["id"])

    if not rows:
        await message.answer("Прав пока нет.")
        return

    lines = ["Твои права:"]
    for row in rows:
        label = RIGHT_LABELS.get(row["right_type"], row["right_type"])
        if row["right_type"] == "unlimited30":
            until = row["ends_at"].strftime("%d.%m.%Y") if row["ends_at"] else "-"
            lines.append(f"- {label}: статус {row['status']}, до {until}")
        else:
            granted = row["granted_units"] or 0
            used = (row["reserved_units"] or 0) + (row["redeemed_units"] or 0) + (row["expired_units"] or 0)
            available = granted - used
            lines.append(f"- {label}: доступно {available} из {granted} (статус {row['status']})")

    lines.append("")
    lines.append("История движений (ЭК-46) - в разработке.")
    await message.answer("\n".join(lines))
