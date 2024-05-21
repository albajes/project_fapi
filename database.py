from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

import settings

engine = create_async_engine(settings.DATABASE_URL, future=True, echo=True)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db() -> AsyncGenerator:
    try:
        async with async_session() as session:
            yield session
    finally:
        await session.close()
