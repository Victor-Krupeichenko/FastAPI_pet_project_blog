from fastapi import HTTPException, status
from api_databases.address_db import _URL_DATABASE
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(_URL_DATABASE, future=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_async_session():
    """Асинхронное получение сессии"""
    async with async_session() as session:
        yield session


# исключение, которое возникает при неверном запросе
data_is_not_valid = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Data is not valid"
)

PAGE = 1  # Указывает на текущую страницу
LIMIT = 9  # Указывает количество записей на странице
