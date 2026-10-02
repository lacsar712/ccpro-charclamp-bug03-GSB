from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from charclamp.domain.models import Base

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://charclamp:charclamp@127.0.0.1:6150/charclamp",
)
DATABASE_URL_SYNC = os.environ.get(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg2://charclamp:charclamp@127.0.0.1:6150/charclamp",
)

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

sync_engine = create_engine(DATABASE_URL_SYNC, echo=False)
SyncSessionLocal = sessionmaker(sync_engine, expire_on_commit=False, class_=Session)


def sync_create_all() -> None:
    Base.metadata.create_all(sync_engine)
    # create_all 不补已有表的列；旧卷里的 clamps 缺 lock_version，
    # 用 IF NOT EXISTS 幂等补上，存量行取默认版本 0。
    with sync_engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE clamps "
                "ADD COLUMN IF NOT EXISTS lock_version INTEGER NOT NULL DEFAULT 0"
            )
        )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
