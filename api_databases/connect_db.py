from api_databases.address_db import URL_DATABASE
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(URL_DATABASE, future=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_async_session():
    """Асинхронное получение сессии"""
    async with async_session() as session:
        yield session
