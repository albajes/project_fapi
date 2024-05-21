from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_filter import FilterDepends
from fastapi_pagination.links import Page

from starlette import status
from starlette.authentication import requires
from starlette.requests import Request

from api.filters import UserFilter
from api.permissions import Permissions
from api.schemas import UserResponseDetail, UserUpdate, UserCreate, UserResponse

user_router = APIRouter()


@user_router.get("/all", response_model=Page[UserResponseDetail])
async def get_all_users(manager: Annotated[Permissions, Depends()],
                        user_filter: Annotated[UserFilter, FilterDepends(UserFilter)]):
    return await manager.user_manager.get_all_users(user_filter)


@user_router.get("/{user_id}", response_model=UserResponseDetail)
async def get_user(user_id: UUID, manager: Annotated[Permissions, Depends()]):
    user = await manager.user_manager.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    return user


@user_router.patch("/{user_id}", response_model=UserResponseDetail)
@requires(['authenticated'])
async def update_user(user_id: UUID, body: UserUpdate, request: Request,
                      manager: Annotated[Permissions, Depends()]):
    if user_id != request.user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You have no rights')

    if body.is_empty():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Set the required fields')

    updated_user = await manager.user_manager.update_user(body.clear())
    if updated_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    return updated_user


@user_router.post("/", response_model=UserResponse)
async def create_user(body: UserCreate, manager: Annotated[Permissions, Depends()]):
    return await manager.user_manager.create_user(name=body.name, email=body.email, password=body.password)


@user_router.delete("/{user_id}")
@requires(['authenticated'])
async def delete_user(user_id: UUID, request: Request, manager: Annotated[Permissions, Depends()]):

    if user_id != request.user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You have no rights')

    deleted_user_id = await manager.user_manager.delete_user(user_id)

    if deleted_user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    return {'id': deleted_user_id}
