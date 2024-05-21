import uuid
import datetime

from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP, Boolean, Integer, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class BlogAuthors(Base):
    __tablename__ = 'blog_authors'

    author_id = Column(ForeignKey('users.id'), primary_key=True, nullable=False)
    blog_id = Column(ForeignKey('blogs.id', ondelete='CASCADE'), primary_key=True, nullable=False)


class Likes(Base):
    __tablename__ = 'likes'

    user_id = Column(ForeignKey('users.id'), primary_key=True, nullable=False)
    post_id = Column(ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True, nullable=False)


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    likes = relationship('Post', secondary='likes', back_populates='likes', lazy='selectin')
    owner_blogs = relationship('Blog', back_populates='owner', lazy='selectin')
    author_blogs = relationship('Blog', secondary='blog_authors', back_populates='authors',  lazy='selectin')
    author_posts = relationship('Post', back_populates='author', lazy='selectin')
    author_comments = relationship('Comment', back_populates='authors', lazy='selectin')


class Blog(Base):
    __tablename__ = 'blogs'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, unique=True)
    description = Column(Text, default='')
    created_at = Column(TIMESTAMP, default=datetime.datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    owner = relationship('User', back_populates='owner_blogs', lazy='selectin')
    authors = relationship('User', secondary='blog_authors', back_populates='author_blogs', lazy='selectin')
    posts = relationship('Post', back_populates='blog', lazy='selectin')


class Post(Base):
    __tablename__ = 'posts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    blog_id = Column(UUID(as_uuid=True), ForeignKey('blogs.id', ondelete='CASCADE'), nullable=False)
    title = Column(String, nullable=False, unique=True)
    body = Column(Text, default='')
    is_published = Column(Boolean(), default=True)
    created_at = Column(TIMESTAMP, default=datetime.datetime.now)
    likes = relationship('User', secondary='likes', back_populates='likes', lazy='selectin')
    views = Column(Integer, default=0)
    author = relationship('User', back_populates='author_posts', lazy='selectin')
    blog = relationship('Blog', back_populates='posts', lazy='selectin')
    comments = relationship('Comment', back_populates='posts', lazy='selectin')


class Comment(Base):
    __tablename__ = 'comments'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    post_id = Column(UUID(as_uuid=True), ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.datetime.now)
    posts = relationship('Post', back_populates='comments', lazy='selectin')
    authors = relationship('User', back_populates='author_comments', lazy='selectin')
