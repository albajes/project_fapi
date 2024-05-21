from jose import jwt, JWTError
from starlette.authentication import AuthenticationBackend, AuthCredentials
from starlette.requests import Request

from api.user.login_handlers import _get_user_by_email
from database import async_session
from settings import SECRET_KEY, ALGORITHM_TOKEN


class BearerTokenAuthBackend(AuthenticationBackend):

    async def authenticate(self, request: Request):
        if 'Authorization' not in request.headers:
            return None

        auth = request.headers['Authorization']
        try:
            token_type, access_token = auth.split()
            if token_type.lower() != 'bearer':
                return None
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM_TOKEN])
        except (ValueError, UnicodeDecodeError, JWTError):
            return None

        email: str = payload.get('sub')
        if email is None:
            return None
        db = async_session()
        user = await _get_user_by_email(email=email, db=db)
        await db.close()
        if user is None:
            return None
        return AuthCredentials(['authenticated']), user
