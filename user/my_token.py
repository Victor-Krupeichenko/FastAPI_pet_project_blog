# pip install "python-jose[cryptography]"
from fastapi import Depends, HTTPException, status, Request
from jose import jwt, JWTError
from src.settings_env import SECRET_KEY_TOKEN, ALGORITHM_TOKEN
from datetime import datetime, timedelta
from sqlalchemy import select
from src.api_models import User
from user.token_from_cookies import OAuth2PasswordBearerWithCookie

ACCESS_TOKEN_EXPIRE_DAYS = 1
NAME_COOKIES = "my_app_cookies"

oauth2_scheme = OAuth2PasswordBearerWithCookie(token_url="/user/login", cookies=NAME_COOKIES)


def create_access_token(data: dict):
    """Создание токена"""
    expire = datetime.now() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)  # Устанавливаем срок действия токена
    encoded_jwt = jwt.encode({**data, "exp": expire}, key=SECRET_KEY_TOKEN, algorithm=ALGORITHM_TOKEN)  # Кодируем токен
    return encoded_jwt  # Возвращаем закодированный токен


async def get_current_user(request: Request, protect: str = Depends(oauth2_scheme)):
    """Получение текущего пользователя"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        token = request.cookies.get(NAME_COOKIES)
        scheme = token.split(" ")[1]
        payload = jwt.decode(scheme, key=SECRET_KEY_TOKEN, algorithms=ALGORITHM_TOKEN)
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    current_user = select(User.username).select_from(User).filter(User.username == username)
    if current_user is None:
        raise credentials_exception
    return username  # Возвращаем имя текущего пользователя
