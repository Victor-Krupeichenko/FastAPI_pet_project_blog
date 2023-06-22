from pydantic import BaseModel, EmailStr, validator
from email_validator import validate_email


class UserSchema(BaseModel):
    username: str
    password: str
    email: EmailStr

    @validator("email")
    def validate_email(cls, email):
        validate_email(email)
        return email.lower()

    class Config:
        orm_mode = True
