"""Root django-ninja API for the saiddit project."""
from ninja import NinjaAPI

from posts.api import router as posts_router
from saiddit.auth import router as auth_router
from saiddit.errors import register_error_handlers
from space.api import router as space_router

api = NinjaAPI(title='saiddit', version='1.0.0')

register_error_handlers(api)

api.add_router('/auth/', auth_router, tags=['auth'])
api.add_router('/posts/', posts_router, tags=['posts'])
api.add_router('/spaces/', space_router, tags=['spaces'])
