from pydantic import BaseModel
from typing import Text


class PostScheme(BaseModel):
    title: str
    content: Text
    category_id: int

    class Config:
        orm_mode = True


class AdminPostScheme(BaseModel):
    published: bool = True
