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

    return await login(request.app.get('connection_users'), request, username, password_hash)


async def register_user(request) -> Response:
    data = await request.json()
    user_type = data.get('user_type')
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    try:
        error = create_user(request.app.get('connection_users'), name=name, user_type=user_type, username=username, password_hash=password_hash)
    except:
        return error_response('Не удалось подключение к базе данных')
    # todo обработка результатов регистрации
    # todo тут имеет место дубликация запросов при создании пользователя и сразу за этим - логин
    if error:
        return error_response(error)

    # todo залогиниться под новым пользователем
    return await login(request.app.get('connection_users'), request, username, password_hash)


async def orders_list(request) -> Response:
    try:
        open_orders = get_open_orders(request.app.get('connection_orders'))
    except:
        return error_response('Не удалось подключение к базе данных')
    return success_response(open_orders)


async def users_list(request) -> Response:
    users_type = request.query.get('users_type')
    try:
        users = await get_users(request.app.get('pool_users'), users_type)
    except:
        return error_response('Не удалось подключение к базе данных')
    return success_response(users)


async def dummy(request) -> Response:
    return Response(text='dummy')
