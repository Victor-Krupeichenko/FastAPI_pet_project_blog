from pydantic import BaseModel, validator
from fastapi import Form


class CategoryScheme(BaseModel):
    """Схема валидации поля у категории"""
    title: str

    @validator("title")
    def validate_title(cls, value):
        if len(value) < 3:
            return {
                "message": f"category: {value} is incorrect, the title category must be at least 3 characters long",
                "value": value}
        return value

    @classmethod
    def as_form(cls, title: str = Form(...)):
        return cls(title=title)

    class Config:
        orm_mode = True


class ResponseCategoryScheme(BaseModel):
    id: int
    title: str

    class Config:
        orm_mode = True
