from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from api.models import User
from api.managers import UserManager
from api.schemas import Token
from auth import create_access_token, Hash

login_router = APIRouter()


@login_router.post('/', response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), manage: UserManager = Depends(UserManager)):
    user = await authenticate_user(form_data.username, form_data.password, manage)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect email or password')
    access_token = create_access_token(data={'sub': user.email, 'other_custom_data': user.name})
    return Token(token_type='bearer', access_token=access_token)


async def authenticate_user(email: str, password: str, manage: UserManager) -> User | None:
    user = await manage.get_user_by_email(email=email)
    if user is None:
        return None
    if not Hash.verify_password(password=password, hashed_pass=user.password):
        return None
    return user


async def _get_user_by_email(email: str, db: AsyncSession) -> User | None:
    async with db as session:
        async with session.begin():
            user_manage = UserManager(session)
            return await user_manage.get_user_by_email(email=email)
