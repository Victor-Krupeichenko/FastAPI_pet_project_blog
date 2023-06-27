from typing import Optional
from fastapi import Form
from pydantic import BaseModel, validator, errors
from pydantic.networks import validate_email


class UserSchema(BaseModel):
    """Схема для создания пользователя"""
    username: str
    password: str
    email: str

    @validator("email")
    def validate_email(cls, value):
        """Валидация поля email"""
        try:
            validate_email(value)
        except errors.EmailError:
            return {"message": "Email is not valid"}
        return value.lower()

    @validator("username")
    def validate_username(cls, value):
        """Валидация поля username"""
        if len(value) < 3:
            return {"message": f"The {value} is incorrect, the name must be at least 3 characters long"}
        elif len(value) > 35:
            return {"message": f"The {value} is incorrect, the length of the name must exceed 35 characters"}
        return value

    @validator("password")
    def validate_password(cls, value):
        """Валидация поля password"""
        if len(value) < 7:
            return {"message": "Password must be at least 7 characters long"}
        elif not value.isalnum():
            return {"message": "Password must contain only letters and numbers"}
        return value

    @classmethod
    def as_form(cls, username: str = Form(...), password: str = Form(...), email: str = Form(...)):
        return cls(username=username, password=password, email=email)

    class Config:
        orm_mode = True


class AdminUserScheme(BaseModel):
    """Схема для обновления поля группы у пользователя"""
    group: Optional[str] = "CLIENT"

    class Config:
        orm_mode = True
