from datetime import datetime
from typing import Optional

from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import Field

from api.models import User, Blog, Post


class UserFilter(Filter):
    name__in: Optional[list[str]] = Field(default=None, alias='names')

    class Constants(Filter.Constants):
        model = User

    class Config:
        populate_by_name = True


class BlogFilter(Filter):
    title__ilike: Optional[str] = Field(default=None, alias='title')
    owner_id: Optional[str] = Field(default=None, alias='owner_id')
    created_at__gte: Optional[datetime] = Field(default=None, alias='after_date')
    created_at__lte: Optional[datetime] = Field(default=None, alias='before_date')

    class Constants(Filter.Constants):
        model = Blog

    class Config:
        populate_by_name = True


class PostFilter(Filter):
    title__ilike: Optional[str] = Field(default=None, alias='title')
    author_id: Optional[str] = Field(default=None, alias='author_id')
    created_at__gte: Optional[datetime] = Field(default=None, alias='after_date')
    created_at__lte: Optional[datetime] = Field(default=None, alias='before_date')
    order_by: Optional[list[str]]

    class Constants(Filter.Constants):
        model = Post

    class Config:
        populate_by_name = True
