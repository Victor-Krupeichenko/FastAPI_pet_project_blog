from fastapi import APIRouter, Depends, status, HTTPException
from src.api_models import Post
from sqlalchemy.ext.asyncio import AsyncSession
from api_databases.connect_db import get_async_session
from post.schemes import PostScheme
from sqlalchemy import insert
from user.my_token import get_current_user

router = APIRouter(
    prefix="/post", tags=["Post"]
)


@router.post("/create_post")
async def create_post(
        post: PostScheme,
        session: AsyncSession = Depends(get_async_session),
        current_user: dict = Depends(get_current_user)
):
    """Создание записи"""
    try:
        query = insert(Post).values(
            title=post.title,
            content=post.content,
            author=current_user,
            category_id=post.category_id
        )

        await session.execute(query)
        await session.commit()
        response = {
            "status": status.HTTP_201_CREATED,
            "data": {**post.dict(), "author": current_user},
            "detail": None
        }
        return response

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data is not valid"
        )
