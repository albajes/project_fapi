from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi_filter import FilterDepends
from fastapi_pagination.links import Page
from starlette import status
from starlette.authentication import requires
from starlette.exceptions import HTTPException
from starlette.requests import Request

from api.filters import PostFilter
from api.managers import PostManager
from api.permissions import Permissions
from api.schemas import PostCreate, PostResponse, PostResponseDetail, PostUpdate

post_router = APIRouter()


@post_router.get('/all', response_model=Page[PostResponseDetail])
async def get_all_posts(manager: Annotated[PostManager, Depends()],
                        post_filter: Annotated[PostFilter, FilterDepends(PostFilter)],
                        author: Annotated[str, None] = None,
                        order_by: Annotated[str, None] = None):
    posts = await manager.get_all_posts(author, order_by, post_filter)
    if posts is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Post does not exist')
    return posts


@post_router.get('/{post_id}', response_model=PostResponseDetail)
async def get_post(post_id: UUID, manager: Annotated[PostManager, Depends()]):
    post = await manager.get_post(post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Post does not exist')
    post = await manager.change_views(post.views + 1, post_id)
    return post


@post_router.post('/', response_model=PostResponse)
@requires(['authenticated'])
async def create_post(body: PostCreate, request: Request,
                      manager: Annotated[Permissions, Depends()]):
    await manager.create_post_permission(blog_id=body.blog_id, user=request.user)
    return await manager.post_manager.create_post(body, request.user)


@post_router.patch('/{post_id}', response_model=PostResponseDetail)
@requires(['authenticated'])
async def update_post(body: PostUpdate, request: Request, post_id: UUID,
                      manager: Annotated[Permissions, Depends()]):
    await manager.update_or_delete_post_permission(post_id=post_id, user=request.user)
    if body.is_empty():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Set the required fields')
    return await manager.post_manager.update_post(post_id, body.clear())


@post_router.delete("/{post_id}")
@requires(['authenticated'])
async def delete_post(post_id: UUID, request: Request,
                      manager: Annotated[PostManager, Depends()],
                      permission: Permissions = Depends(Permissions)):
    await permission.update_or_delete_post_permission(post_id=post_id, user=request.user)
    deleted_post_id = await manager.delete_post(post_id)
    return {'id': deleted_post_id}


@post_router.patch("/{post_id}/like_button", response_model=PostResponseDetail)
@requires(['authenticated'])
async def add_or_remove_like(post_id: UUID, request: Request,
                             manager: Annotated[PostManager, Depends()]):
    return await manager.set_or_remove_like(post_id=post_id, user_id=request.user.id)
