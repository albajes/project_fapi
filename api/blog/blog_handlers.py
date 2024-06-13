import uuid
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination.links import Page
from starlette import status
from starlette.authentication import requires
from starlette.exceptions import HTTPException
from starlette.requests import Request

from api.filters import BlogFilter
from api.managers import BlogManager
from api.permissions import Permissions
from api.schemas import BlogResponse, BlogCreate, AddOrRemoveAuthorToBlog, BlogResponseDetail, BlogUpdate

blog_router = APIRouter()


@blog_router.get("/all", response_model=Page[BlogResponseDetail])
async def get_all_blogs(manager: Annotated[BlogManager, Depends()],
                        blog_filter: Annotated[BlogFilter, FilterDepends(BlogFilter)],
                        author: Annotated[str, None] = None,
                        order_by: Annotated[str, None] = None):
    blogs = await manager.get_all_blogs(author, order_by, blog_filter)
    return blogs


@blog_router.get("/{blog_id}", response_model=BlogResponseDetail)
async def get_blog(blog_id: uuid.UUID, manager: Annotated[BlogManager, Depends()]):
    blog = await manager.get_blog(blog_id)
    if blog is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Blog does not found')
    return blog


@blog_router.post("/", response_model=BlogResponse)
@requires(['authenticated'])
async def create_blog(body: BlogCreate, request: Request, manager: Annotated[BlogManager, Depends()]):
    return await manager.create_blog(body=body, owner_id=request.user.id)


@blog_router.patch("/{blog_id}", response_model=BlogResponseDetail)
@requires(['authenticated'])
async def update_blog(body: BlogUpdate, blog_id: UUID, request: Request,
                      manager: Annotated[Permissions, Depends()]):
    if body.is_empty():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Set the required fields')
    await manager.blog_permission(blog_id=blog_id, user_id=request.user.id)
    return await manager.blog_manager.update_blog(blog_id, body.clear())


@blog_router.post("/{blog_id}/add_author", response_model=BlogResponseDetail)
@requires(['authenticated'])
async def add_author_to_blog(body: AddOrRemoveAuthorToBlog, request: Request,
                             blog_id: UUID,
                             manager: Annotated[Permissions, Depends()]):
    await manager.blog_permission(blog_id, request.user.id)
    return await manager.blog_manager.create_blog_author(blog_id=blog_id, author_id=body.author_id)


@blog_router.post("/{blog_id}/remove_author", response_model=BlogResponseDetail)
@requires(['authenticated'])
async def remove_author_from_blog(body: AddOrRemoveAuthorToBlog, request: Request,
                                  blog_id: UUID,
                                  manager: Annotated[Permissions, Depends()]):
    await manager.blog_permission(blog_id, request.user.id)
    return await manager.blog_manager.delete_blog_author(blog_id=blog_id, author_id=body.author_id)


@blog_router.delete("/{blog_id}")
@requires(['authenticated'])
async def delete_blog(blog_id: UUID, request: Request,
                      manager: Annotated[Permissions, Depends()]):
    await manager.blog_permission(blog_id, request.user.id)
    deleted_blog_id = await manager.blog_manager.delete_blog(blog_id)
    return {'blog_id': deleted_blog_id}
