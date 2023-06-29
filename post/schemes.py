from pydantic import BaseModel, validator
from typing import Text
from fastapi import Form


class PostScheme(BaseModel):
    """Схема для валидации полей при создании поста"""
    title: str
    content: Text
    category_id: int

    @validator("title")
    def validate_title(cls, value):
        """Валидация поля title"""
        if len(value) < 3:
            return {"message": f"title: {value} is incorrect, the title must be at least 3 characters long",
                    "value": value}
        elif len(value) > 250:
            return {"message": f"title: {value} is incorrect, the title of the name must exceed 250 characters",
                    "value": value}
        return value

    @validator("content")
    def validate_content(cls, value):
        """Валидация поля content"""
        if len(value) < 25:
            return {"message": f"content: {value} is incorrect, the content must be at least 25 characters long",
                    "value": value}
        return value

    @validator("category_id")
    def validate_category(cls, value):
        """Валидация поля category_id"""
        if value == 0 or not value:
            return {"message": f"category: is incorrect", "value": value}
        return value

    @classmethod
    def is_form(cls, title: str = Form(...), content: Text = Form(...), category_id: int = Form(...)):
        return cls(title=title, content=content, category_id=category_id)

    class Config:
        orm_mode = True


class AdminPostScheme(BaseModel):
    published: bool = True
