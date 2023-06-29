from fastapi import APIRouter, HTTPException, Depends, status, Response
from sqlalchemy.exc import IntegrityError
from user.my_token import create_access_token, NAME_COOKIES
from src.api_models import User
from user.schemas import UserSchema, AdminUserScheme, AuthUserScheme
from api_databases.connect_db import get_async_session, data_is_not_valid
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.hash import pbkdf2_sha256
from sqlalchemy import insert, select, update
from user.my_token import get_current_user

router = APIRouter(
    prefix="/user", tags=["User"]
)


async def field_validation(field: dict) -> list:
    """Валидация полей формы"""
    errors_list = list()
    for key in field.keys():
        if isinstance(field[key], dict):
            for value in field[key].values():
                errors_list.append(value)
    return errors_list


@router.post("/user_create")
async def user_create(user: UserSchema = Depends(UserSchema.as_form),
                      session: AsyncSession = Depends(get_async_session)
                      ):
    """Создание пользователя"""
    user_data = user.dict()
    # Проверка наличия ошибок валидации полей
    errors_list = await field_validation(user_data)
    if errors_list:
        return {"errors": errors_list}
    msg = 'A user with the same name or email already exists'
    try:
        # Проверка наличия пользователя в базе данных с таким именем
        query = select(User).filter(User.username == user_data["username"].title())
        result = await session.execute(query)
        user = result.scalar()
        if user:
            errors_list.append(msg)
            return {"errors": errors_list}

        # Добавление (регистрация) пользователя в базу данных
        hashed_password = pbkdf2_sha256.hash(user_data["password"])
        new_user = insert(User).values(
            username=user_data["username"].title(),
            password=hashed_password,
            email=user_data["email"]
        )
        await session.execute(new_user)
        await session.commit()
    # Если email неуникальны (Пользователь с таким email уже есть в базе данных)
    except IntegrityError:
        errors_list.append(msg)
        return {"errors": errors_list}
    # Перехватываем все непредвиденные исключения
    except Exception:
        raise data_is_not_valid

    # При успешной регистрации возвращаем словарь
    response = {
        "status": status.HTTP_201_CREATED,
        "username": user_data["username"].title(),
        "password": user_data["password"],
        "email": user_data["email"]
    }
    return response


@router.post("/login")
async def login(
        response: Response,
        user_form: AuthUserScheme = Depends(AuthUserScheme.as_form),
        session: AsyncSession = Depends(get_async_session)
):
    """Авторизация пользователя"""
    user_data = user_form.dict()
    # Проверка наличия ошибок валидации полей
    errors_list = await field_validation(user_data)
    if errors_list:
        return {"errors": errors_list}

    # Аутентификация пользователя
    query = select(User).filter(User.username == user_data["username"].title())
    user = await session.scalar(query)
    if not user:
        msg = f"User: {user_data['username']} not found'"
        errors_list.append(msg)
        return {"errors": errors_list}
    elif not pbkdf2_sha256.verify(user_data["password"], user.password):
        msg = f"Password: '{user_data['password']}' invalid password"
        errors_list.append(msg)
        return {"errors": errors_list}
    # Создание токена
    jwt_token = create_access_token(data={"sub": user.username})
    # Сохранение токена в cookie
    response.set_cookie(key=NAME_COOKIES, value=f"Bearer {jwt_token}", httponly=True)
    return {
        "token": jwt_token,
        "username": user.username,
    }


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
            raise data_is_not_valid
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"You {current_user['username']}: are not a superuser"
    )


@router.delete("/delete_user/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user),
                      session: AsyncSession = Depends(get_async_session)
                      ):
    """Удаление пользователя"""
    if current_user is None:
        return data_is_not_valid
    if current_user["group"] == "ADMIN" or current_user["user_id"] == user_id:
        try:
            query = select(User).filter(User.id == user_id)
            user_delete = await session.execute(query)
            await session.delete(user_delete.scalar())
            await session.commit()
            return {
                "status": status.HTTP_204_NO_CONTENT,
                "detail": "User Deleted!"
            }

        except Exception:
            raise data_is_not_valid
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin: You are not allowed to delete other users"
        )


@router.put("/update_user/{user_id}")
async def update_user(user_id: int, response: Response, user: UserSchema = Depends(UserSchema.as_form),
                      current_user: dict = Depends(get_current_user),
                      session: AsyncSession = Depends(get_async_session)
                      ):
    """Обновление пользователя"""
    user_data = user.dict()
    errors_list = await field_validation(user_data)
    if errors_list:
        return {"errors": errors_list}
    if current_user["user_id"] == user_id or current_user["group"] == "ADMIN":
        q_username = select(User.username).filter(User.username == user.username)
        q_email = select(User.email).filter(User.email == user.email)
        if user.username != current_user["username"]:
            exists = await session.execute(q_username)
            result = exists.scalar()
            if result is not None:
                msg = f"The user: {user.username} is already registered."
                errors_list.append(msg)
                return {"errors": errors_list}
        if user.email != current_user["email"]:
            exists = await session.execute(q_email)
            result = exists.scalar()
            if result is not None:
                msg = f"User with email: {user.email} is already registered."
                errors_list.append(msg)
                return {"errors": errors_list}
        hashed_password = pbkdf2_sha256.hash(user.password)
        try:
            user_update = update(User).values(
                username=user.username,
                password=hashed_password,
                email=user.email
            ).filter(User.id == user_id)
            await session.execute(user_update)
            await session.commit()
            # Создание токена
            jwt_token = create_access_token(data={"sub": user.username})
            # Сохранение токена в cookie
            response.set_cookie(key=NAME_COOKIES, value=f"Bearer {jwt_token}", httponly=True)
            return {
                "token": jwt_token,
                "username": user.username,
            }
        except Exception:
            raise data_is_not_valid

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Username does not match yours"
    )


@router.get("/logout")
async def user_logout(response: Response, current_user: dict = Depends(get_current_user)):
    """Выход пользователя из приложения"""
    response.delete_cookie(NAME_COOKIES)
    return {"message": f'User: {current_user["username"]} logged out'}
