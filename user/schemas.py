from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from email_validator import validate_email


class UserSchema(BaseModel):
    """Схема для создания пользователя"""
    username: str
    password: str
    email: EmailStr

    @validator("email")
    def validate_email(cls, email):
        validate_email(email)
        return email.lower()

    class Config:
        orm_mode = True


class AdminUserScheme(BaseModel):
    """Схема для обновления поля группы у пользователя"""
    group: Optional[str] = "CLIENT"

    class Config:
        orm_mode = True
