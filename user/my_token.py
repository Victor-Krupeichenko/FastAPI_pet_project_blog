# pip install "python-jose[cryptography]"
from fastapi import Depends, HTTPException, status, Request
from jose import jwt, JWTError
from src.settings_env import SECRET_KEY_TOKEN, ALGORITHM_TOKEN
from datetime import datetime, timedelta
from sqlalchemy import select
from src.api_models import User
from api_databases.connect_db import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

ACCESS_TOKEN_EXPIRE_DAYS = 1
NAME_COOKIES = "my_app_cookies"


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")


def create_access_token(data: dict):
    """Создание токена"""
    expire = datetime.now() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)  # Устанавливаем срок действия токена
    encoded_jwt = jwt.encode({**data, "exp": expire}, key=SECRET_KEY_TOKEN, algorithm=ALGORITHM_TOKEN)  # Кодируем токен
    return encoded_jwt  # Возвращаем закодированный токен


async def get_current_user(request: Request, session: AsyncSession = Depends(get_async_session)):
    """Получение текущего пользователя"""
    credentials_exception = None
    try:
        token = request.cookies.get(NAME_COOKIES)
        if token is not None:
            scheme = token.split(" ")[1]
            payload = jwt.decode(scheme, key=SECRET_KEY_TOKEN, algorithms=ALGORITHM_TOKEN)
            username = payload.get("sub")
        else:
            return credentials_exception
    except JWTError:
        return credentials_exception
    user = select(User.username, User.group, User.is_active, User.id, User.email).select_from(User).filter(
        User.username == username)
    if user is None:
        return credentials_exception
    temporary = await session.execute(user)
    try:
        temporary_user = temporary.all()[0]  # Попадаем внутрь списка
        current_user = dict(zip(["username", "group", "is_active", "user_id", "email"], temporary_user))
        # Возвращаем словарь с информацией о текущего пользователя
        return current_user
    except IndexError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='This user does not exist'
        )
