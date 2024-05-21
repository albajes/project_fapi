from typing import Annotated

from fastapi import HTTPException, Depends
from sqlalchemy.dialects.postgresql import UUID
from starlette import status

from api.managers import BlogManager, UserManager, PostManager
from api.models import User


#  depends managers
class Permissions:

    def __init__(self, blog_manager: Annotated[BlogManager, Depends()],
                 post_manager: Annotated[PostManager, Depends()],
                 user_manager: Annotated[UserManager, Depends()]):
        self.blog_manager = blog_manager
        self.post_manager = post_manager
        self.user_manager = user_manager

    async def blog_permission(self, blog_id: UUID, user_id: UUID):
        blog = await self.blog_manager.get_blog(blog_id=blog_id)

        if blog is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='Blog does not found')

        if blog.owner_id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='You are not owner of this blog')

    async def create_post_permission(self, blog_id: UUID, user: User):
        blog = await self.blog_manager.get_blog_authors(blog_id=blog_id, user_id=user.id)
        if blog is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='You are not owner or author of this blog')

    async def update_or_delete_post_permission(self, post_id: UUID, user: User):
        post = await self.post_manager.get_post(post_id=post_id)

        if post is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='Post does not found')

        if post.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='You are not author of this post')
