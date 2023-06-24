from pydantic import BaseModel


class CategoryScheme(BaseModel):
    title: str

    class Config:
        orm_mode = True


class ResponseCategoryScheme(BaseModel):
    id: int
    title: str

    class Config:
        orm_mode = True
