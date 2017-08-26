import hashlib
import os

from .. import settings

from aiohttp import web
from aiohttp.web import Response

from .storage import login, create_user, get_open_orders, get_users
from ..utils import success_response, error_response


# Хэндлеры

async def index(request) -> Response:
    with open(os.path.join(settings.BASE_DIR, 'frontend', 'index.html'), 'r') as f:
        html = f.read()
    return web.Response(body=html, content_type='text/html', charset='utf-8')


async def user_login(request) -> Response:
    data = await request.json()
    username = data.get('username')
    password = data.get('password')
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    return await login(request, username, password_hash)


async def register_user(request) -> Response:
    data = await request.json()
    user_type = data.get('user_type')
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    error = create_user(name=name, user_type=user_type, username=username, password_hash=password_hash)
    # todo обработка результатов регистрации
    # todo тут имеет место дубликация запросов при создании пользователя и сразу за этим - логин
    if error:
        return error_response(error)

    # todo залогиниться под новым пользователем
    return await login(request, username, password_hash)


async def orders_list(request) -> Response:
    open_orders = get_open_orders()
    return success_response(open_orders)


async def users_list(request) -> Response:
    users_type = request.query.get('users_type')
    users = await get_users(users_type)
    return success_response(users)


async def dummy(request) -> Response:
    return Response(text='dummy')
