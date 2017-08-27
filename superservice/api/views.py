import hashlib
import os
try:
    import ujson as json_lib
except:
    import json as json_lib

from pymysql.err import IntegrityError

from aiohttp import web
from aiohttp.web import Response

from aiohttp_session import get_session

from .. import settings
from .storage import check_user, create_user, get_open_orders, get_users
from ..utils import success_response, error_response, login_required, save_user_to_session
from ..exceptions import ConnectionNotFound, WrongUserType, UsernameAlreadyExists, WrongLoginOrPassword, DBConsistencyError


# Хэндлеры

async def index(request) -> Response:
    with open(os.path.join(settings.BASE_DIR, 'frontend', 'index.html'), 'r') as f:
        html = f.read()
    return web.Response(body=html, content_type='text/html', charset='utf-8')


async def login_user(request) -> Response:
    data = await request.json(loads=json_lib.loads)
    login = data.get('login')
    password = data.get('password')
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    try:
        user = await check_user(request.app.get('pool_users'), login, password_hash)
    except ConnectionNotFound:
        return error_response('Не удалось подключение к базе данных')
    except WrongLoginOrPassword:
        return error_response('Неправильное имя пользователя или пароль')
    except DBConsistencyError:
        return error_response('Ошибка в базе данных: больше одного пользователя с одинаковым именем пользователя')

    save_user_to_session(await get_session(request), user)

    return success_response('Вы вошли как {}'.format(user.get('name')))


async def register_user(request) -> Response:
    data = await request.json(loads=json_lib.loads)
    user_type = data.get('user_type')
    name = data.get('name')
    login = data.get('login')
    password = data.get('password')
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    try:
        user = await create_user(request.app.get('pool_users'), name, user_type, login, password_hash)
    except ConnectionNotFound:
        return error_response('Не удалось подключение к базе данных')
    except WrongUserType:
        return error_response('Неверно указан user_type')
    except (UsernameAlreadyExists, IntegrityError):
        return error_response('Пользователь с таким именем уже зарегистрирован')

    save_user_to_session(await get_session(request), user)

    return success_response('Пользователь успешно зарегистрирован')


async def orders_list(request) -> Response:
    try:
        open_orders = await get_open_orders(request.app.get('pool_orders'))
    except ConnectionNotFound:
        return error_response('Не удалось подключение к базе данных')
    return success_response(open_orders)


@login_required
async def users_list(request) -> Response:
    users_type = request.query.get('users_type')
    try:
        users = await get_users(request.app.get('pool_users'), users_type)
    except ConnectionNotFound:
        return error_response('Не удалось подключение к базе данных')
    except WrongUserType:
        return error_response('Неверно указан user_type')
    return success_response(users)


async def dummy(request) -> Response:
    return Response(text='dummy')
