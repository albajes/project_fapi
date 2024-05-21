from datetime import datetime
import uuid
from enum import Enum
from typing import Optional, List

from fastapi import HTTPException
from pydantic import BaseModel, EmailStr, constr, Field, field_serializer
from starlette import status

from api.models import Post, User


class UpdateMixin:
    def is_empty(self: BaseModel):
        return not self.clear()

    def clear(self: BaseModel):
        return self.dict(exclude_none=True)


class TunedModel(BaseModel):

    def validate_id(self, request):
        if self.id != request.user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You have no rights')

        return self

    class Config:
        from_attributes = True


class UserResponse(TunedModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    is_active: bool


class BlogResponse(TunedModel):
    """Используется при создании блога впервые"""
    id: uuid.UUID
    title: str
    description: str
    created_at: datetime
    updated_at: datetime


class BlogResponseDetail(BlogResponse):
    """Используется при запросе конкретного блога"""
    owner: UserResponse = None
    authors: List[UserResponse] = []


class BlogCreate(BaseModel):
    """Используется при создании блога"""
    title: str
    description: Optional[str] = None


class UserResponseDetail(UserResponse):
    """Используется при запросах конкретного пользователя"""
    owner_blogs: List[BlogResponse] = []
    author_blogs: List[BlogResponse] = []


class UserCreate(BaseModel):
    """Используется при создании пользователя"""
    name: str
    email: EmailStr
    password: str


class UserUpdate(TunedModel, UpdateMixin):
    """Используется при обновлении пользователя"""
    name: Optional[constr(min_length=3)] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class Token(BaseModel):
    """Используется при авторизации пользователя"""
    token_type: str
    access_token: str


class AddOrRemoveAuthorToBlog(TunedModel):
    """Используется при добавлении автора в блог"""
    author_id: uuid.UUID


class BlogUpdate(TunedModel, UpdateMixin):
    """Используется при обновлении блога"""
    title: Optional[constr(min_length=5)] = None
    description: Optional[constr(min_length=10)] = None


class PostUpdate(TunedModel, UpdateMixin):
    """Используется при обновлении поста"""
    title: str = None
    body: constr(min_length=10) = None


class PostCreate(PostUpdate):
    """Используется при создании поста"""
    blog_id: uuid.UUID


class CommentResponse(TunedModel):
    """Используется в ответе при создании комментария"""
    id: uuid.UUID
    author_id: uuid.UUID
    post_id: uuid.UUID
    body: str
    created_at: datetime


class PostResponse(TunedModel):
    """Используется при создании/получении поста"""

    id: uuid.UUID
    title: str
    body: str
    author_id: uuid.UUID
    blog_id: uuid.UUID
    is_published: bool
    created_at: datetime
    views: int


class PostResponseDetail(PostResponse):
    """Используется при получении поста"""
    likes: List[UserResponse] = []
    author: UserResponse
    blog: BlogResponse

    @field_serializer('likes')
    def serialize_likes(self, likes):
        return len(likes)


class CommentUpdate(TunedModel, UpdateMixin):
    """Используется при обновлении комментария"""
    body: str


class CommentCreate(CommentUpdate):
    """Используется при создании комментария"""
    post_id: uuid.UUID


class CommentResponseDetail(CommentResponse):
    posts: PostResponseDetail
    authors: UserResponse
