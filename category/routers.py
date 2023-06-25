from fastapi import APIRouter, Depends, HTTPException, status
from src.api_models import Category
from api_databases.connect_db import get_async_session, data_is_not_valid
from sqlalchemy.ext.asyncio import AsyncSession
from category.schemes import CategoryScheme, ResponseCategoryScheme
from sqlalchemy import insert, select, update
from user.my_token import get_current_user
from typing import List

router = APIRouter(
    prefix="/category", tags=["Category"]
)


@router.post("/create_category")
async def create_category(category: CategoryScheme, session: AsyncSession = Depends(get_async_session),
                          current_user: dict = Depends(get_current_user)
                          ):
    """Создание категории"""
    if current_user["group"] != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only administrator can add categories"
        )
    try:
        query = insert(Category).values(title=category.title)
        await session.execute(query)
        await session.commit()
        response = {
            "status": status.HTTP_201_CREATED,
            "data": {**category.dict()},
            "detail": "success"
        }
        return response
    except Exception:
        raise data_is_not_valid


@router.put("/update_category/{category_id}")
async def update_category(category_id: int, category: CategoryScheme,
                          session: AsyncSession = Depends(get_async_session),
                          current_user: dict = Depends(get_current_user)
                          ):
    """Обновление категории"""
    if current_user["group"] != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only administrator can update categories"
        )
    q_category = select(Category.title).filter(Category.title == category.title)
    exists = await session.execute(q_category)
    result = exists.scalar()
    if result is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"the category with the name: {category.title} already exists"
        )
    try:
        category_update = update(Category).values(title=category.title).filter(Category.id == category_id)
        await session.execute(category_update)
        await session.commit()
        response = {
            "status": status.HTTP_202_ACCEPTED,
            "data": {**category.dict()},
            "detail": "success"
        }
        return response
    except Exception:
        raise data_is_not_valid


@router.get("/category/{category_id}")
async def get_category(category_id: int, session: AsyncSession = Depends(get_async_session)):
    """Получение конкретной категории"""
    try:
        category = select(Category).filter(Category.id == category_id)
        my_category = await session.execute(category)
        result = my_category.scalar()
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Category ID: {category_id} not found')
        return {
            "status": status.HTTP_200_OK,
            "data": result,
            "detail": None
        }
    except Exception:
        raise data_is_not_valid


@router.get("/categories_all", response_model=List[ResponseCategoryScheme], status_code=status.HTTP_200_OK)
async def get_all_categories(session: AsyncSession = Depends(get_async_session)):
    """Получение всех категорий"""
    try:
        category = select(Category)
        categories_all = await session.execute(category)
        result = categories_all.scalars().all()
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Categories not found')
        # return {
        #     "status": status.HTTP_200_OK,
        #     "data": result.all(),
        #     "detail": None
        # }
        return result
    except Exception:
        raise data_is_not_valid


@router.delete("/delete_category/{category_id}")
async def delete_category(category_id: int, current_user: dict = Depends(get_current_user),
                          session: AsyncSession = Depends(get_async_session)
                          ):
    """Удаление категории"""
    if current_user["group"] == "ADMIN":
        try:
            query = select(Category).filter(Category.id == category_id)
            category_delete = await session.execute(query)
            await session.delete(category_delete.scalar())
            await session.commit()
            return {"message": f"Category ID: {category_id} DELETED!"}
        except Exception:
            raise data_is_not_valid

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Only administrator can delete categories"
    )
