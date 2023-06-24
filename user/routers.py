from fastapi import APIRouter, HTTPException, Depends, status, Response
from sqlalchemy.exc import IntegrityError
from fastapi.security import OAuth2PasswordRequestForm
from user.my_token import create_access_token, NAME_COOKIES
from src.api_models import User
from user.schemas import UserSchema, AdminUserScheme
from api_databases.connect_db import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.hash import pbkdf2_sha256
from sqlalchemy import insert, select, update, delete
from user.my_token import get_current_user

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


@router.patch("/update_user_group/{user_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_user(
        user_id: int, user: AdminUserScheme,
        current_user: dict = Depends(get_current_user), session: AsyncSession = Depends(get_async_session)
):
    """Обновление поля group у пользователя"""
    if current_user["group"] == "ADMIN":
        try:
            update_values = user.dict(exclude_unset=True)  # Исключаем поля которые небыли переданы
            query = update(User).filter(User.id == user_id).values(**update_values)
            await session.execute(query)
            await session.commit()
            return {"message": "group changed successful to ADMIN"}
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Data is not valid")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"You {current_user['username']}: are not a superuser"
    )


@router.delete("/delete_user/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user),
                      session: AsyncSession = Depends(get_async_session)
                      ):
    """Удаление пользователя"""
    if current_user["group"] == "ADMIN" or current_user["user_id"] == user_id:
        try:
            query = delete(User).filter(User.id == user_id)
            await session.execute(query)
            await session.commit()
            response = {
                "status": status.HTTP_204_NO_CONTENT,
                "detail": "User Deleted!"
            }
            return response
        except Exception:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data is not valid"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin: You are not allowed to delete other users"
        )


@router.put("/update_user/{user_id}")
async def update_user(user_id: int, user: UserSchema, current_user: dict = Depends(get_current_user),
                      session: AsyncSession = Depends(get_async_session)
                      ):
    """Обновление пользователя"""
    if current_user["user_id"] == user_id or current_user["group"] == "ADMIN":
        q_username = select(User.username).filter(User.username == user.username)
        q_email = select(User.email).filter(User.email == user.email)
        if user.username != current_user["username"]:
            exists = await session.execute(q_username)
            result = exists.scalar()
            if result is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"The user: {user.username} is already registered."
                )
        if user.email != current_user["email"]:
            exists = await session.execute(q_email)
            result = exists.scalar()
            if result is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with email: {user.email} is already registered."
                )
        hashed_password = pbkdf2_sha256.hash(user.password)
        try:
            user_update = update(User).values(
                username=user.username,
                password=hashed_password,
                email=user.email
            ).filter(User.id == user_id)
            await session.execute(user_update)
            await session.commit()
            response = {
                "status": status.HTTP_202_ACCEPTED,
                "data": {**user.dict()},
                "detail": "success"
            }
            return response
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Data is not valid"
            )

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Username does not match yours"
    )


@router.post("/logout")
async def user_logout(response: Response, current_user: dict = Depends(get_current_user)):
    """Выход пользователя из приложения"""
    username = current_user["username"]
    response.delete_cookie(NAME_COOKIES)
    return {"message": f"Пользователь {username} -> вышел из сети"}
