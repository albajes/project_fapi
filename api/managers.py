from fastapi import Depends
from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_pagination.ext.async_sqlalchemy import paginate
from sqlalchemy import select, update, delete, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID
from typing import Union

from starlette import status
from starlette.exceptions import HTTPException

from api.models import User, Blog, BlogAuthors, Post, Comment, Likes
from api.schemas import BlogCreate, PostCreate, CommentCreate
from auth import Hash
from abc import ABC

from database import get_db


class Manager(ABC):
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db_session = db


class UserManager(Manager):

    async def get_all_users(self, user_filter):
        statement = user_filter.filter(select(User).where(User.is_active == True))
        users = await paginate(self.db_session, statement)
        return users

    async def get_user(self, id: UUID) -> Union[User, None]:
        statement = select(User).where(and_(User.is_active == True, User.id == id))
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)
        user = result.scalar()
        return user

    async def get_user_by_email(self, email: str) -> Union[User, None]:
        statement = select(User).where(and_(User.is_active == True, User.email == email))
        result = await self.db_session.execute(statement)
        user = result.scalar()
        return user

    async def create_user(self,
                          name: str,
                          email: str,
                          password: str) -> User:
        new_user = User(
            name=name,
            email=email,
            password=Hash.get_hashed_password(password)
        )
        async with self.db_session.begin():
            self.db_session.add(new_user)
            await self.db_session.flush()
        return new_user

    async def update_user(self, params: dict) -> User | None:
        user_id = params.pop('id')
        statement = update(User).where(and_(User.is_active == True, User.id == user_id)).values(params).returning(User)
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)
        user = result.scalar()
        return user

    async def delete_user(self, user_id: UUID) -> UUID | None:
        statement = update(User).where(User.id == user_id).values(is_active=False).returning(User.id)
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)
        user_id = result.scalar()
        return user_id


class BlogManager(Manager):

    async def get_all_blogs(self, author: str | None, order_by: str | None, blog_filter: Filter):
        async with self.db_session.begin():
            if author:
                blogs = await paginate(self.db_session,
                                       select(Blog).where(Blog.authors.any(User.name == author)).order_by(Blog.created_at.desc()))

            elif order_by:
                blogs = await paginate(self.db_session, blog_filter.sort(select(Blog)))

            else:
                blogs = await paginate(self.db_session,
                                       blog_filter.filter(select(Blog).order_by(Blog.created_at.desc())))
        return blogs

    async def get_blog(self, blog_id: UUID) -> Blog | None:
        statement = select(Blog).where(Blog.id == blog_id)
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)
        blog = result.scalar()
        return blog

    async def create_blog(self, body: BlogCreate, owner_id: UUID) -> Blog:
        new_blog = Blog(
            title=body.title,
            description=body.description,
            owner_id=owner_id
        )
        async with self.db_session.begin():
            self.db_session.add(new_blog)
            try:
                await self.db_session.flush()
            except IntegrityError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail='Blog with this title already exist')
            new_blog_author = BlogAuthors(author_id=owner_id,
                                          blog_id=new_blog.id)
            self.db_session.add(new_blog_author)
            await self.db_session.flush()
        return new_blog

    async def create_blog_author(self, author_id: UUID, blog_id: UUID) -> Blog:
        item = await self.get_blog_authors(blog_id=blog_id, user_id=author_id)
        if item is None:
            new_blog_author = BlogAuthors(author_id=author_id,
                                          blog_id=blog_id)
            async with self.db_session.begin():
                self.db_session.add(new_blog_author)
                try:
                    await self.db_session.flush()
                except IntegrityError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail='You are trying to add a non-existent user to authors')
        blog = await self.get_blog(blog_id=blog_id)
        return blog

    async def delete_blog_author(self, author_id: UUID, blog_id: UUID) -> None:
        statement = delete(BlogAuthors).where(and_(BlogAuthors.blog_id == blog_id, BlogAuthors.author_id == author_id)).\
            returning(BlogAuthors.blog_id)
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)
        if result.scalar() is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='This blog has not authors with this id')

        blog = await self.get_blog(blog_id=blog_id)
        return blog

    async def get_blog_authors(self, blog_id: UUID, user_id: UUID) -> BlogAuthors | None:
        statement = select(BlogAuthors).where(and_(BlogAuthors.blog_id == blog_id, BlogAuthors.author_id == user_id))
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)
        blog_authors = result.scalar()
        return blog_authors

    async def update_blog(self, blog_id: UUID, params: dict) -> Blog:
        statement = update(Blog).where(Blog.id == blog_id).values(params).returning(Blog)
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)
        blog = result.scalar()
        return blog

    async def delete_blog(self, blog_id: UUID) -> UUID:
        statement = delete(Blog).where(Blog.id == blog_id).returning(Blog.id)
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)
        deleted_blog_id = result.scalar()
        return deleted_blog_id


class PostManager(Manager):

    async def get_all_posts(self, author: str | None, order_by: str | None, post_filter: Filter):
        async with self.db_session.begin():
            if author:
                posts = await paginate(self.db_session,
                                       select(Post).where(and_(Post.author.has(User.name == author), Post.is_published == True)).
                                       order_by(Post.created_at.desc()))
            elif order_by:
                posts = await paginate(self.db_session,
                                       post_filter.sort(select(Post).where(Post.is_published == True)))
            else:
                posts = await paginate(self.db_session,
                                       post_filter.filter(select(Post).where(Post.is_published == True).
                                                          order_by(Post.created_at.desc())))
        return posts

    async def get_post(self, post_id: UUID) -> Post | None:
        statement = select(Post).where(and_(Post.id == post_id, Post.is_published == True))
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)
        post = result.scalar()
        return post

    async def create_post(self, data: PostCreate, author: User) -> Post:
        new_post = Post(blog_id=data.blog_id, author_id=author.id, title=data.title, body=data.body)
        async with self.db_session.begin():
            self.db_session.add(new_post)
            try:
                await self.db_session.flush()
            except IntegrityError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail='Post with this title already exist')
        return new_post

    async def set_or_remove_like(self, post_id: UUID, user_id: UUID):
        post = await self.get_post(post_id=post_id)
        if post is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail='Post does not exist')

        statement = select(Likes).where(and_(Likes.post_id == post_id, Likes.user_id == user_id))
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)

        if result.scalar():
            statement = delete(Likes).where(and_(Likes.post_id == post_id, Likes.user_id == user_id))
            async with self.db_session.begin():
                await self.db_session.execute(statement)
        else:
            like = Likes(post_id=post_id, user_id=user_id)
            async with self.db_session.begin():
                self.db_session.add(like)
                await self.db_session.flush()
        await self.db_session.close()

        post1 = await self.get_post(post_id=post_id)
        return post1

    async def change_views(self, views: int, post_id: UUID) -> Post:
        statement = update(Post).where(and_(Post.id == post_id, Post.is_published == True)).\
            values({'views': views}).returning(Post)
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)
        post = result.scalar()
        return post

    async def update_post(self, post_id: UUID, data: dict) -> Post:
        statement = update(Post).where(Post.id == post_id).values(data).returning(Post)
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)
        updated_post = result.scalar()
        return updated_post

    async def delete_post(self, post_id: UUID) -> UUID:
        statement = delete(Post).where(Post.id == post_id).returning(Post.id)
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)
        post_id = result.scalar()
        return post_id


class CommentManager(Manager):

    async def get_comments(self, post_id: UUID):
        statement = select(Comment).where(Comment.post_id == post_id)
        async with self.db_session.begin():
            result = await self.db_session.scalars(statement)
        comments = result.all()
        return comments

    async def create_comment(self, data: CommentCreate, author: User) -> Comment | None:
        new_comment = Comment(post_id=data.post_id, author_id=author.id, body=data.body)
        async with self.db_session.begin():
            try:
                self.db_session.add(new_comment)
                await self.db_session.flush()
            except IntegrityError:
                return None
        return new_comment

    async def update_comment(self, comment_id: UUID, data: dict, user_id: UUID) -> Comment:
        statement = update(Comment).where(and_(Comment.id == comment_id, Comment.author_id == user_id)).\
            values(data).returning(Comment)
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)
        updated_comment = result.scalar()
        return updated_comment

    async def delete_comment(self, comment_id: UUID, user_id: UUID) -> UUID:
        statement = delete(Comment).where(and_(Comment.id == comment_id, Comment.author_id == user_id)).\
            returning(Comment.id)
        async with self.db_session.begin():
            result = await self.db_session.execute(statement)
        comment_id = result.scalar()
        return comment_id
