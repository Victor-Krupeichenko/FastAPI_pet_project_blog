from fastapi import APIRouter, Depends, status, HTTPException
from math import ceil
from sqlalchemy.orm import joinedload, selectinload
from src.api_models import Post
from sqlalchemy.ext.asyncio import AsyncSession
from api_databases.connect_db import get_async_session, data_is_not_valid, PAGE, LIMIT
from post.schemes import PostScheme, AdminPostScheme, SearchPostScheme
from sqlalchemy import insert, select, update, and_, func
from user.my_token import get_current_user
from user.routers import field_validation

router = APIRouter(
    prefix="/post", tags=["Post"]
)

count_date = None


async def get_count_date_all(session: AsyncSession = Depends(get_async_session)):
    """Получает общее количество опубликованных данных"""
    query = select(func.count()).select_from(Post).filter(Post.published)
    exists = await session.scalar(query)
    global count_date
    count_date = exists


async def pagination(
        query, limit, count_data, session: AsyncSession = Depends(get_async_session)
):
    """Пагинация"""
    # Получение количества страниц (округление в большую сторону)
    total_pages = ceil(count_data / limit)
    # Определяет показывать пагинацию или нет (Своего рода такой флаг True или False)
    show_pagination = total_pages > 1
    # Выполняет запрос на получения записей
    all_posts = await session.execute(query)
    result = all_posts.scalars().all()
    response = {
        "data": result,
        "total_pages": total_pages,
        "show_pagination": show_pagination
    }
    return response


async def my_range(page, limit):
    """Диапазон для получения данных для пагинации"""
    start = (page - 1) * limit
    end = start + limit
    return start, end


async def content_error(row_dict: dict, key: str):
    """Получает данные если они были введены некорректно"""
    content_error_dict = {}
    for dict_key in row_dict:
        if isinstance(row_dict[dict_key], dict):
            content_error_dict[dict_key] = row_dict[dict_key][key]
    return content_error_dict


@router.post("/create_post")
async def create_post(
        post: PostScheme = Depends(PostScheme.as_form),
        session: AsyncSession = Depends(get_async_session),
        current_user: dict = Depends(get_current_user)
):
    """Создание записи"""
    if not current_user:
        return {"errors": "Not authorized"}
    post_data = post.dict()
    errors_list = await field_validation(post_data)
    if errors_list:
        data_is_not_correct = await content_error(post_data, "value")
        response = {
            "errors": errors_list,
            "not_correct": data_is_not_correct,
            "post_data": post_data
        }
        return response
    try:
        query = insert(Post).values(**post.dict(), user_id=current_user["user_id"])
        await session.execute(query)
        await session.commit()
    except Exception:
        raise data_is_not_valid

    response = {
        "status": status.HTTP_201_CREATED,
        "data": {**post.dict()},
        "detail": None
    }
    return response


@router.get("/all_posts", status_code=status.HTTP_200_OK)
async def get_all_posts(page: int = PAGE, limit: int = LIMIT,
                        session: AsyncSession = Depends(get_async_session)):
    """Получение всех опубликованных записей"""
    try:
        # Получаем общее количество данных
        if count_date is None:
            await get_count_date_all(session)
        # Получение записей в диапазоне
        start, end = await my_range(page, limit)
        qu = select(Post).options(selectinload(Post.category)).filter(
            Post.published
        ).order_by(Post.id.desc()).slice(start, end)
        # Пагинация
        result = await pagination(query=qu, count_data=count_date, limit=limit, session=session)
        return result
    except Exception:
        raise data_is_not_valid


@router.get("/one_post/{post_id}", status_code=status.HTTP_200_OK)
async def get_one_post(post_id: int, session: AsyncSession = Depends(get_async_session)):
    """Получение конкретной записи"""
    query = select(Post).options(joinedload(Post.category), joinedload(Post.user)).filter(Post.id == post_id)
    post = await session.execute(query)
    result = post.scalar()
    if result is not None:
        return result
    raise data_is_not_valid


@router.put("/update_post/{post_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_post(post_id: int, post: PostScheme = Depends(PostScheme.as_form),
                      current_user: dict = Depends(get_current_user),
                      session: AsyncSession = Depends(get_async_session)
                      ):
    """Обновление конкретной записи"""
    query = select(Post).filter(Post.id == post_id)
    exists = await session.execute(query)
    result = exists.scalar()
    if result is None:
        return {"errors": f"Post ID: {post_id} not found"}
    post_data = post.dict()
    errors_list = await field_validation(post_data)
    if errors_list:
        data_is_not_correct = await content_error(post_data, "value")
        response = {
            "errors": errors_list,
            "not_correct": data_is_not_correct,
            "post_data": post_data
        }
        return response
    if current_user["group"] == "ADMIN" or result.user_id == current_user["user_id"]:
        try:
            post_update = update(Post).values(**post.dict()).filter(Post.id == post_id)
            await session.execute(post_update)
            await session.commit()
        except Exception:
            raise data_is_not_valid
    else:
        msg = {"errors": "You are not the author of this post"}
        errors_list.append(msg)
        return errors_list
    return {**post.dict()}


@router.patch("/update_post_published/{post_id}", status_code=status.HTTP_202_ACCEPTED)
async def update_post_published(post_id: int, post: AdminPostScheme, current_user: dict = Depends(get_current_user),
                                session: AsyncSession = Depends(get_async_session)
                                ):
    """Опубликовывает запись (published ставить в True)"""
    if current_user["group"] == "ADMIN":
        try:
            update_published = post.dict(exclude_unset=True)
            query = update(Post).values(**update_published).filter(Post.id == post_id)
            print(query)
            await session.execute(query)
            await session.commit()
            return {"messages": f"Post ID: {post_id} published"}
        except Exception:
            raise data_is_not_valid
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Only an Administrator can change the status of a post"
    )


@router.get("/category_post_all/{category_id}", status_code=status.HTTP_200_OK)
async def category_post_all(category_id: int, page: int = PAGE, limit: int = LIMIT,
                            session: AsyncSession = Depends(get_async_session)):
    """Получение всех записей у конкретной категории"""
    try:
        # Получение количества записей у категории
        post_count = select(func.count(Post.id)).select_from(Post).filter(
            and_(Post.category_id == category_id, Post.published))
        exists = await session.scalar(post_count)
        # Получение записей в диапазоне
        start, end = await my_range(page, limit)
        posts_for_category = select(Post).options(selectinload(Post.category)).filter(
            and_(Post.category_id == category_id, Post.published)).order_by(Post.id.desc()).slice(start, end)
        # Пагинация
        result = await pagination(query=posts_for_category, count_data=exists, limit=limit, session=session)
        return result
    except Exception:
        raise data_is_not_valid


@router.delete("/delete_post/{post_id}")
async def delete_post(post_id: int, session: AsyncSession = Depends(get_async_session),
                      current_user: dict = Depends(get_current_user)
                      ):
    """Удаление записи"""
    query = select(Post).filter(Post.id == post_id)
    post = await session.execute(query)
    post_delete = post.scalar()
    if not current_user:
        return {"messages": "No authorization"}
    if not post:
        return {"messages": f"Post ID: {post_id} not found"}
    if current_user["group"] != "ADMIN" and post_delete.user_id != current_user["user_id"]:
        return {"messages": "You are not the post author or administrator"}
    await session.delete(post_delete)
    await session.commit()
    return {"messages": f"Post ID: {post_id} Delete"}


@router.post("/search/")
async def search_post(
        post_title: SearchPostScheme = Depends(SearchPostScheme.as_form),
        session: AsyncSession = Depends(get_async_session),
        page: int = PAGE, limit: int = LIMIT
):
    """Поиск"""
    post_search = post_title.search.lower()
    post_count = select(func.count(Post.id)).select_from(Post).filter(
        and_(func.lower(Post.title).like(f"%{post_search}%"), Post.published))
    exists = await session.scalar(post_count)
    if exists == 0:
        response = {
            "not_found": f"Post {post_title.search} not found"
        }
        return response
    # Получение записей в диапазоне
    start, end = await my_range(page, limit)
    post_search = select(Post).options(selectinload(Post.category)).filter(
        and_(Post.published, func.lower(Post.title).like(f"%{post_search}%"))).order_by(Post.id.desc()).slice(start,
                                                                                                              end)
    # Пагинация
    result = await pagination(query=post_search, count_data=exists, limit=limit, session=session)
    return result
