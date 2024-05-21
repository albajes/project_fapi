from fastapi import FastAPI, APIRouter
from fastapi_pagination import add_pagination
from starlette.middleware.authentication import AuthenticationMiddleware

from api.blog.blog_handlers import blog_router
from api.comment.comment_handlers import comment_router
from api.post.post_handlers import post_router
from api.user.login_handlers import login_router
from api.user.user_handlers import user_router
from middleware import BearerTokenAuthBackend

app = FastAPI()
add_pagination(app)

router = APIRouter()
router.include_router(user_router, prefix='/users', tags=['users'])
router.include_router(login_router, prefix='/login', tags=['login'])
router.include_router(blog_router, prefix='/blogs', tags=['blogs'])
router.include_router(post_router, prefix='/posts', tags=['posts'])
router.include_router(comment_router, prefix='/comments', tags=['comments'])

app.include_router(router)

app.add_middleware(AuthenticationMiddleware, backend=BearerTokenAuthBackend())
