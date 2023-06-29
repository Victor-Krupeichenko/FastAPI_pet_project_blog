from fastapi import APIRouter, Request, Depends, status, responses
from fastapi.templating import Jinja2Templates
from api_databases.connect_db import PAGE
from user.my_token import get_current_user
from post.routers import (
    get_all_posts,
    get_one_post,
    category_post_all
)
from category.routers import (
    get_all_categories,
    get_category
)
from user.routers import (
    user_create,
    login,
    user_logout,
    delete_user,
    update_user
)
from user.my_token import NAME_COOKIES

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="webapp/templates")
env = templates.env


# Определение фильтра форматирования времени
def format_time(value, format_date="%d-%m-%Y %H:%M:%S"):
    return value.strftime(format_date)


# Определение фильтра для вывода только count первых слов (по умолчанию первых 7 слов)
def word_count(value, count=7):
    words = value.split()[:count]
    return ' '.join(words)


# Регистрация фильтра в экземпляре Environment
env.filters["format_time"] = format_time
env.filters["word_count"] = word_count


@router.get("/")
async def post_all(request: Request, posts=Depends(get_all_posts), categories=Depends(get_all_categories),
                   page: int = PAGE, messages: str = None, current_user=Depends(get_current_user)):
    """Главная страница (вывод всех постов) + пагинация """
    return templates.TemplateResponse("index.html", {
        "request": request, "posts": posts, "categories": categories, "page": page, "messages": messages,
        "current_user": current_user
    })


@router.get("/one_post/{post_id}")
def one_post(request: Request, post=Depends(get_one_post), categories=Depends(get_all_categories),
             current_user=Depends(get_current_user)):
    """Страница детальной информации о записи"""
    return templates.TemplateResponse("detail_post.html", {
        "request": request, "post": post, "categories": categories, "current_user": current_user
    })


@router.get('/category_post_all/{category_id}')
def category_post_all(request: Request, posts=Depends(category_post_all), categories=Depends(get_all_categories),
                      category_title=Depends(get_category), page: int = PAGE, current_user=Depends(get_current_user)):
    """Вывод всех записей у конкретной категории + пагинация"""
    return templates.TemplateResponse("index.html", {
        "request": request, "posts": posts, "categories": categories, "page": page, "category_title": category_title,
        "current_user": current_user
    })


message = "User Register"


@router.get("/registration")
def registration(request: Request):
    """Переход на страницу регистрации"""
    return templates.TemplateResponse("user_auth.html", {"request": request, "msg": message, "logup": True})


@router.post('/registration')
def registration(request: Request, user=Depends(user_create)):
    """Регистрация пользователя"""
    if "errors" in user:
        return templates.TemplateResponse("user_auth.html", {
            "request": request, "msg": message, "errors": user["errors"], "logup": True
        })
    return responses.RedirectResponse('/?messages=Successfully Registration', status_code=status.HTTP_302_FOUND)


msg = "User Login"


@router.get("/login")
def log_in(request: Request):
    """Переход на страницу авторизации"""
    return templates.TemplateResponse("user_auth.html", {"request": request, "msg": msg, "log_in": True})


@router.post("/login")
def log_in(request: Request, user=Depends(login)):
    """Авторизация пользователя"""
    if "errors" in user:
        return templates.TemplateResponse("user_auth.html", {
            "request": request, "errors": user["errors"], "log_in": True, "msg": msg
        })
    response = responses.RedirectResponse(
        f'/?messages=User: {user["username"]} is authorized', status_code=status.HTTP_302_FOUND
    )
    response.set_cookie(key=NAME_COOKIES, value=f'Bearer {user["token"]}', httponly=True)
    return response


@router.get("/logout")
def log_out(user=Depends(user_logout)):
    """Выход пользователя"""
    response = responses.RedirectResponse(f'/?messages={user["message"]}', status_code=status.HTTP_302_FOUND)
    response.delete_cookie(NAME_COOKIES)
    return response


@router.get("/delete/{user_id}", dependencies=[Depends(delete_user)])
def user_delete():
    """Удаление пользователя"""
    response = responses.RedirectResponse(f'/', status_code=status.HTTP_302_FOUND)
    response.delete_cookie(NAME_COOKIES)
    return response


@router.get("/update_user")
def user_update(request: Request, current_user=Depends(get_current_user)):
    up_user = "Update User"
    return templates.TemplateResponse("user_auth.html", {
        "request": request, "msg": up_user, "update_user": True, "current_user": current_user
    })


@router.post('/update_user/{user_id}')
def user_update(request: Request, user: dict = Depends(update_user), current_user=Depends(get_current_user)):
    """Обновление пользователя"""
    if "errors" in user:
        return templates.TemplateResponse("user_auth.html", {
            "request": request, "errors": user["errors"], "update_user": True, "current_user": current_user
        })
    response = responses.RedirectResponse(f'/?messages=Updated user to: {user["username"]}',
                                          status_code=status.HTTP_302_FOUND)
    response.set_cookie(key=NAME_COOKIES, value=f'Bearer {user["token"]}', httponly=True)
    return response
