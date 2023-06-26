from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from api_databases.connect_db import PAGE, LIMIT
from post.routers import (
    get_all_posts,
    get_one_post,
    category_post_all
)
from category.routers import (
    get_all_categories,
    get_category
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
                   page: int = PAGE,
                   limit: int = LIMIT):
    """Главная страница (вывод всех постов)"""
    return templates.TemplateResponse("index.html",
                                      {"request": request, "posts": posts["data"], "count_data": posts["count_data"],
                                       "categories": categories, "page": page,
                                       "limit": limit, "start": posts["start"], "end": posts["end"]})


@router.get("/one_post/{post_id}")
def one_post(request: Request, post=Depends(get_one_post), categories=Depends(get_all_categories)):
    """Страница детальной информации о записи"""
    return templates.TemplateResponse("detail_post.html",
                                      {"request": request, "post": post, "categories": categories})


@router.get('/category_post_all/{category_id}')
def category_post_all(request: Request, posts=Depends(category_post_all), categories=Depends(get_all_categories),
                      category_title=Depends(get_category)):
    """Вывод всех записей у конкретной категории"""
    return templates.TemplateResponse("index.html",
                                      {"request": request, "posts": posts, "categories": categories,
                                       "category_title": category_title})
