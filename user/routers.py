from fastapi import APIRouter, HTTPException, Depends, status, Response
from sqlalchemy.exc import IntegrityError
from fastapi.security import OAuth2PasswordRequestForm
from user.my_token import create_access_token, NAME_COOKIES
from src.api_models import User
from user.schemas import UserSchema
from api_databases.connect_db import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.hash import pbkdf2_sha256
from sqlalchemy import insert, select

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
        await session.commit()
        response = {
            "status": status.HTTP_201_CREATED,
            "data": {**user.dict()},
            "detail": "success"
        }
        return response
    except IntegrityError:
        # Если username или email неуникальны (Пользователь с таким именем или email уже есть в базе данных)
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


@router.post("/login")
async def login(
        response: Response,
        request: OAuth2PasswordRequestForm = Depends(),
        session: AsyncSession = Depends(get_async_session)
):
    """Авторизация пользователя"""
    query = select(User).filter(User.username == request.username)
    user = await session.scalar(query)
    # Аутентификация пользователя
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User: {request.username} not found'")
    elif not pbkdf2_sha256.verify(request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Password: '{request.password}' invalid password"
        )
    # Создание токена
    jwt_token = create_access_token(data={"sub": user.username})
    # Сохранение токена в cookie
    response.set_cookie(key=NAME_COOKIES, value=f"Bearer {jwt_token}", httponly=True)
    return {"message": f"{user.username} -> login"}
