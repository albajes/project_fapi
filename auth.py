import datetime
from datetime import timedelta

from jose import jwt

from settings import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM_TOKEN
from passlib.context import CryptContext

password_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class Hash:

    @staticmethod
    def get_hashed_password(password: str) -> str:
        return password_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed_pass: str) -> bool:
        return password_context.verify(password, hashed_pass)


def create_access_token(data: dict):
    expire = datetime.datetime.now() + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    data.update({'exp': expire})
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM_TOKEN)
    return encoded_jwt
