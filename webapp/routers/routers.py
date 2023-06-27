from fastapi import APIRouter, Request, Depends, responses, status
from fastapi.templating import Jinja2Templates
from api_databases.connect_db import PAGE
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
    user_create
)

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
                   page: int = PAGE, messages: str = None):
    """Главная страница (вывод всех постов) + пагинация """
    return templates.TemplateResponse("index.html",
                                      {"request": request, "posts": posts["data"], "total_pages": posts["total_pages"],
                                       "categories": categories, "page": page,
                                       "show_pagination": posts["show_pagination"], "messages": messages})


@router.get("/one_post/{post_id}")
def one_post(request: Request, post=Depends(get_one_post), categories=Depends(get_all_categories)):
    """Страница детальной информации о записи"""
    return templates.TemplateResponse("detail_post.html",
                                      {"request": request, "post": post, "categories": categories})


@router.get('/category_post_all/{category_id}')
def category_post_all(request: Request, posts=Depends(category_post_all), categories=Depends(get_all_categories),
                      category_title=Depends(get_category), page: int = PAGE):
    """Вывод всех записей у конкретной категории + пагинация"""
    return templates.TemplateResponse("index.html",
                                      {"request": request, "posts": posts["data"], "total_pages": posts["total_pages"],
                                       "categories": categories, "page": page,
                                       "show_pagination": posts["show_pagination"],
                                       "category_title": category_title})


message = "User Register"


@router.get("/registration")
def registration(request: Request):
    return templates.TemplateResponse("user_create.html", {"request": request, "msg": message})


@router.post('/registration')
def registration(request: Request, user=Depends(user_create)):
    """Регистрация пользователя"""
    if "errors" in user:
        return templates.TemplateResponse("user_create.html",
                                          {"request": request, "msg": message, "errors": user["errors"]})
    return responses.RedirectResponse('/?messages=Successfully Registration', status_code=status.HTTP_302_FOUND)
