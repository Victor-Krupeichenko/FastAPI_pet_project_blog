from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.exc import IntegrityError

from src.api_models import User
from user.schemas import UserSchema
from api_databases.connect_db import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.hash import pbkdf2_sha256
from sqlalchemy import insert

router = APIRouter(
    prefix="/user", tags=["User"]
)


@router.post("/user_create")
async def user_create(user: UserSchema, session: AsyncSession = Depends(get_async_session)):
    """Создание Пользователя"""
    try:
        hashed_password = pbkdf2_sha256.hash(user.password)
        query = insert(User).values(username=user.username, password=hashed_password, email=user.email)
        await session.execute(query)
    except IntegrityError:
        # Если username или email уже не уникальны (Пользователь с таким именем или email уже есть в базе данных)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with the same name or email already exists"
        )
    except Exception:
        # Все остальные исключения
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data is not valid"
        )
    else:
        await session.commit()
        response = {
            "status": status.HTTP_201_CREATED,
            "data": {**user.dict()},
            "detail": "success"
        }
        return response
