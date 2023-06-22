from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, TIMESTAMP
from sqlalchemy_utils.types import ChoiceType
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """Модель для создания пользователя"""
    GROUP_OF_USERS = (
        ("ADMIN", "admin"),
        ("CLIENT", "client")
    )
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    username = Column(String(35), nullable=False, index=True, unique=True)
    password = Column(Text, nullable=False)
    email = Column(String, nullable=False, unique=True)
    created = Column(TIMESTAMP, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    group = Column(ChoiceType(choices=GROUP_OF_USERS), default="CLIENT")
    posts = relationship("Post", back_populates="user", cascade="all, delete")


class Post(Base):
    """Модель для создания записи"""
    __tablename__ = "post"
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String, ForeignKey("user.username"), nullable=False)
    created = Column(TIMESTAMP, default=datetime.utcnow)
    published = Column(Boolean, default=False)
    category_id = Column(Integer, ForeignKey("category.id"))
    user = relationship("User", back_populates="posts")
    category = relationship("Category", back_populates="posts")


class Category(Base):
    """Модель категории для записи"""
    __tablename__ = "category"
    id = Column(Integer, primary_key=True)
    title = Column(String(40), nullable=False, unique=True, index=True)
    posts = relationship("Post", back_populates="category")
