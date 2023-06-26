from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import joinedload, selectinload
from src.api_models import Post
from sqlalchemy.ext.asyncio import AsyncSession
from api_databases.connect_db import get_async_session, data_is_not_valid, PAGE, LIMIT
from post.schemes import PostScheme, AdminPostScheme
from sqlalchemy import insert, select, update, and_, func
from user.my_token import get_current_user

router = APIRouter(
    prefix="/post", tags=["Post"]
)

count_date = None


async def get_count_date(session: AsyncSession = Depends(get_async_session)):
    """Получает общее количество опубликованных данных"""
    query = select(func.count()).select_from(Post).filter(Post.published)
    exists = await session.scalar(query)
    global count_date
    count_date = exists


@router.post("/create_post")
async def create_post(
        post: PostScheme,
        session: AsyncSession = Depends(get_async_session),
        current_user: dict = Depends(get_current_user)
):
    """Создание записи"""
    try:
        query = insert(Post).values(**post.dict(), user_id=current_user["user_id"])
        await session.execute(query)
        await session.commit()

        response = {
            "status": status.HTTP_201_CREATED,
            "data": {**post.dict(), "username": current_user["username"]},
            "detail": None
        }
        return response

    except Exception:
        raise data_is_not_valid


@router.get("/all_posts", status_code=status.HTTP_200_OK)
async def get_all_posts(page: int = PAGE, limit: int = LIMIT,
                        session: AsyncSession = Depends(get_async_session)):
    """Получение всех опубликованных записей"""
    try:
        # Получаем общее количество данных
        if count_date is None:
            await get_count_date(session)
        # Пагинация
        start = (page - 1) * limit
        end = start + limit
        qu = select(Post).options(selectinload(Post.category)).filter(
            Post.published
        ).order_by(Post.id.desc()).slice(start, end)
        all_posts = await session.execute(qu)
        result = all_posts.scalars().all()
        response = {
            "data": result,
            "count_data": count_date,
            "start": start,
            "end": end
        }
        return response
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
async def update_post(post_id: int, post: PostScheme, current_user: dict = Depends(get_current_user),
                      session: AsyncSession = Depends(get_async_session)
                      ):
    """Обновление конкретной записи"""
    query = select(Post).filter(Post.id == post_id)
    exists = await session.execute(query)
    result = exists.scalar()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post ID: {post_id} not found"
        )
    if current_user["group"] == "ADMIN" or result.user_id == current_user["user_id"]:
        try:
            post_update = update(Post).values(**post.dict()).filter(Post.id == post_id)
            await session.execute(post_update)
            await session.commit()
            return {**post.dict()}
        except Exception:
            raise data_is_not_valid
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="You are not the author of this post"
    )


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
            return {"message": f"Post ID: {post_id} published"}
        except Exception:
            raise data_is_not_valid
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Only an Administrator can change the status of a post"
    )


@router.get("/category_post_all/{category_id}", status_code=status.HTTP_200_OK)
async def category_post_all(category_id: int, session: AsyncSession = Depends(get_async_session)):
    """Получение всех записей у конкретной категории"""
    category = select(Post).filter(and_(Post.category_id == category_id, Post.published))
    exists = await session.execute(category)
    result = exists.scalars().all()
    return result
