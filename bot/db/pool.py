from pathlib import Path

import asyncpg

_pool: asyncpg.Pool | None = None


async def init_pool(database_url: str) -> asyncpg.Pool:
    global _pool
    _pool = await asyncpg.create_pool(dsn=database_url, min_size=1, max_size=5)
    schema_path = Path(__file__).with_name("schema.sql")
    async with _pool.acquire() as conn:
        await conn.execute(schema_path.read_text(encoding="utf-8"))
    return _pool


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool is not initialized")
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
