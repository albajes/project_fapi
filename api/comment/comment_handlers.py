from typing import Annotated, List
from uuid import UUID
from fastapi import APIRouter, Depends
from starlette import status
from starlette.authentication import requires
from starlette.exceptions import HTTPException
from starlette.requests import Request

from api.managers import CommentManager
from api.schemas import CommentResponse, CommentCreate, CommentUpdate, CommentResponseDetail

comment_router = APIRouter()


@comment_router.get("/from_post/{post_id}", response_model=List[CommentResponse])
async def get_comments_from_post(post_id: UUID,
                                 manager: Annotated[CommentManager, Depends()]):
    comments = await manager.get_comments(post_id=post_id)
    return comments


@comment_router.post('/', response_model=CommentResponse)
@requires(['authenticated'])
async def create_comment(body: CommentCreate, request: Request,
                         manager: Annotated[CommentManager, Depends()]):
    comment = await manager.create_comment(body, request.user)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Post does not found')
    return comment


@comment_router.patch('/{comment_id}', response_model=CommentResponseDetail)
@requires(['authenticated'])
async def update_comment(comment_id: UUID, body: CommentUpdate, request: Request,
                         manager: Annotated[CommentManager, Depends()]):
    if body.is_empty():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Set the required fields')
    comment = await manager.update_comment(comment_id, body.clear(), request.user.id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Comment does not exist')
    return comment


@comment_router.delete("/{comment_id}")
@requires(['authenticated'])
async def delete_comment(comment_id: UUID, request: Request,
                         manager: Annotated[CommentManager, Depends()]):
    deleted_comment_id = await manager.delete_comment(comment_id, request.user.id)
    if deleted_comment_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail='Comment does not exist')
    return {'id': deleted_comment_id}
