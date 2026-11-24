import logging
from contextlib import asynccontextmanager
from datetime import datetime

import asyncpg

log = logging.getLogger(__name__)


class PostgreSQLDB:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    # ==================== CONNECT ====================

    async def connect(
        self,
        host: str = "127.0.0.1",
        port: int = 5432,
        dbname: str = "bonch",
        user: str = "postgres",
        password: str = "DB_PASSWORD",
    ) -> None:
        try:
            self.pool = await asyncpg.create_pool(
                host=host,
                port=port,
                database=dbname,
                user=user,
                password=password,
                min_size=1,
                max_size=10,
            )

            log.info("Connected to PostgreSQL")

        except Exception:
            log.exception("Failed to connect to PostgreSQL")
            raise

    # ==================== CLOSE ====================

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

            log.info("PostgreSQL pool closed")

    # ==================== TRANSACTION ====================

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[asyncpg.Connection]:
        if self.pool is None:
            raise RuntimeError("Database pool is not connected")

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    # ==================== QUERY ====================

    async def execute(self, query: str, *args):
        if self.pool is None:
            raise RuntimeError("Database pool is not connected")

        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        if self.pool is None:
            raise RuntimeError("Database pool is not connected")

        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        if self.pool is None:
            raise RuntimeError("Database pool is not connected")

        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        if self.pool is None:
            raise RuntimeError("Database pool is not connected")

        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def fetchall(self, query: str, *args):
        if self.pool is None:
            raise RuntimeError("Database pool is not connected")

        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
