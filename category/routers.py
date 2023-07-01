from fastapi import APIRouter, Depends, HTTPException, status
from src.api_models import Category, Post
from api_databases.connect_db import get_async_session, data_is_not_valid
from sqlalchemy.ext.asyncio import AsyncSession
from category.schemes import CategoryScheme
from sqlalchemy import insert, select, update, func
from user.my_token import get_current_user
from post.routers import content_error, field_validation

router = APIRouter(
    prefix="/category", tags=["Category"]
)


@router.post("/create_category")
async def create_category(category: CategoryScheme = Depends(CategoryScheme.as_form),
                          session: AsyncSession = Depends(get_async_session),
                          current_user: dict = Depends(get_current_user)
                          ):
    """Создание категории"""
    if current_user["group"] != "ADMIN":
        return {"errors": "Only administrator can add categories"}
    category_data = category.dict()
    errors_list = await field_validation(category_data)
    if errors_list:
        data_is_not_correct = await content_error(category_data, "value")
        response = {
            "errors": errors_list,
            "not_correct": data_is_not_correct,
            "category_data": category_data
        }
        return response
    try:
        query = insert(Category).values(title=category.title)
        await session.execute(query)
        await session.commit()
    except Exception as ex:
        return {"errors": f'{ex}'}
    response = {
        "status": status.HTTP_201_CREATED,
        "data": {**category.dict()},
        "detail": "success"
    }
    return response


@router.put("/update_category/{category_id}")
async def update_one_category(category_id: int, category: CategoryScheme = Depends(CategoryScheme.as_form),
                              session: AsyncSession = Depends(get_async_session),
                              current_user: dict = Depends(get_current_user)
                              ):
    """Обновление категории"""
    if current_user["group"] != "ADMIN":
        return {"errors": "Only administrator can update categories"}
    category_data = category.dict()
    errors_list = await field_validation(category_data)
    if errors_list:
        data_is_not_correct = await content_error(category_data, "value")
        response = {
            "errors": errors_list,
            "not_correct": data_is_not_correct,
            "category_data": category_data,
        }
        return response
    q_category = select(Category.title).filter(Category.title == category.title)
    exists = await session.execute(q_category)
    result = exists.scalar()
    if result is not None:
        response = {
            "errors_title": f"The category with the name: {category.title} already exists",
            "title": category_data["title"]
        }
        return response
    try:
        category_update = update(Category).values(title=category.title).filter(Category.id == category_id)
        await session.execute(category_update)
        await session.commit()
    except Exception as ex:
        return {"errors": f'{ex}'}
    response = {
        "status": status.HTTP_202_ACCEPTED,
        "data": {**category.dict()},
        "detail": "success"
    }
    return response


@router.get("/category/{category_id}")
async def get_category(category_id: int, session: AsyncSession = Depends(get_async_session)):
    """Получение конкретной категории"""
    try:
        category = select(Category).filter(Category.id == category_id)
        my_category = await session.execute(category)
        result = my_category.scalar()
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Category ID: {category_id} not found')
        return result
    except Exception:
        raise data_is_not_valid


@router.get("/categories_all", status_code=status.HTTP_200_OK)
async def get_all_categories(session: AsyncSession = Depends(get_async_session)):
    """Получение только тех категорий, у которых есть опубликованные посты"""
    try:
        category = select(Category.id, Category.title, func.count(Post.id)).join(Category.posts).filter(
            Post.published).group_by(Category.id, Category.title)
        exists = await session.execute(category)
        result = exists.fetchall()
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Categories not found')
        result = [{"category_id": row[0], "category": row[1], "post_count": row[2]} for row in result]
        return result

    except Exception:
        raise data_is_not_valid


@router.delete("/delete_category/{category_id}")
async def delete_category(category_id: int, current_user: dict = Depends(get_current_user),
                          session: AsyncSession = Depends(get_async_session)
                          ):
    """Удаление категории"""
    if not current_user:
        return {"message": "No authorization"}
    if current_user["group"] != "ADMIN":
        return {"messages": "Only administrator can delete categories"}
    try:
        query = select(Category).filter(Category.id == category_id)
        category_delete = await session.execute(query)
        category = category_delete.scalar()
        cat_title = category.title
        if not category:
            return {"messages": f"Category ID: {category_id} not found"}
        await session.delete(category)
        await session.commit()
        return {
            "messages": f"Category ID: {category_id} DELETED!",
            "title": cat_title
        }

    except Exception as ex:
        return {"messages": ex}


@router.get("/categories")
async def categories(session: AsyncSession = Depends(get_async_session)):
    """Получение всех категорий"""
    all_categories = select(Category)
    exists = await session.execute(all_categories)
    result = exists.scalars().all()
    return result
