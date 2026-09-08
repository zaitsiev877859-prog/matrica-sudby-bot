"""Репозиторий каркаса. Реализует только СОБ-01/СОБ-02 (профиль, демо-партия) и чтение прав.
Остальные события 04c (резервации, оплаты, генерация) будут добавлены на следующем этапе.
"""

import asyncpg


async def get_specialist_by_telegram_id(conn: asyncpg.Connection, telegram_id: int):
    return await conn.fetchrow(
        "SELECT * FROM specialists WHERE telegram_id = $1", telegram_id
    )


async def create_specialist(conn: asyncpg.Connection, telegram_id: int):
    # СОБ-01: Первый /start -> Профиль не заполнен. Идемпотентно по telegram_id.
    return await conn.fetchrow(
        """
        INSERT INTO specialists (telegram_id, status)
        VALUES ($1, 'profile_incomplete')
        ON CONFLICT (telegram_id) DO UPDATE SET telegram_id = EXCLUDED.telegram_id
        RETURNING *
        """,
        telegram_id,
    )


async def complete_profile(
    conn: asyncpg.Connection,
    specialist_id,
    display_name: str,
    alias: str | None,
    contact_value: str | None,
):
    # СОБ-02: Профиль сохранён -> Активен; одна демо-партия ДН-07 на 2 единицы + начисление ДН-08.
    async with conn.transaction():
        specialist = await conn.fetchrow(
            """
            UPDATE specialists
            SET display_name = $2, alias = $3, contact_value = $4,
                status = 'active', profile_completed_at = now(), updated_at = now()
            WHERE id = $1
            RETURNING *
            """,
            specialist_id, display_name, alias, contact_value,
        )

        existing_demo = await conn.fetchval(
            "SELECT id FROM rights_balances WHERE specialist_id = $1 AND right_type = 'demo'",
            specialist_id,
        )
        if existing_demo is None:
            right_id = await conn.fetchval(
                """
                INSERT INTO rights_balances (specialist_id, right_type, granted_units, status, source)
                VALUES ($1, 'demo', 2, 'active', 'signup')
                RETURNING id
                """,
                specialist_id,
            )
            await conn.execute(
                """
                INSERT INTO rights_ledger (right_id, entry_type, units, idempotency_key, reason, initiator_type)
                VALUES ($1, 'grant', 2, $2, 'Регистрация профиля', 'system')
                ON CONFLICT (idempotency_key) DO NOTHING
                """,
                right_id, f"signup-demo-{specialist_id}",
            )

        return specialist


async def get_rights_summary(conn: asyncpg.Connection, specialist_id):
    return await conn.fetch(
        """
        SELECT right_type, granted_units, reserved_units, redeemed_units, expired_units,
               status, starts_at, ends_at
        FROM rights_balances
        WHERE specialist_id = $1
        ORDER BY created_at
        """,
        specialist_id,
    )
