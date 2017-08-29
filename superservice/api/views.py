import hashlib
import os
try:
    import ujson as json_lib
except:
    import json as json_lib

from pymysql.err import IntegrityError, DataError

from aiohttp import web
from aiohttp.web import Response

from aiohttp_session import get_session

from .. import settings
from .storage import check_user, create_user, get_open_orders, get_users, create_order, find_order, fulfill_order
from ..utils import success_response, error_response, login_required, save_user_to_session
from .. import exceptions


async def index(request) -> Response:
    with open(os.path.join(settings.BASE_DIR, 'frontend', 'index.html'), 'r') as f:
        html = f.read()
    return web.Response(body=html, content_type='text/html', charset='utf-8')


@login_required()
async def logout_user(request) -> Response:
    session = await get_session(request)
    session.invalidate()
    return success_response('Вы успешно вышли из системы')


async def login_user(request) -> Response:
    try:
        data = await request.json(loads=json_lib.loads)
    except ValueError:
        return error_response('Ошибка входных данных')

    try:
        login = data['login']
        password = data['password']
        password_hash = hashlib.sha256(password.encode()).hexdigest()
    except KeyError:
        return error_response('Недостаточно входных данных')
    except AttributeError:
        return error_response('Ошибка входных данных')

    try:
        user = await check_user(request.app.get('pool_users'), login, password_hash)
    except exceptions.MySQLConnectionNotFound:
        return error_response('Не удалось подключение к базе данных')
    except exceptions.WrongLoginOrPassword:
        return error_response('Неправильное имя пользователя или пароль')
    except exceptions.DBConsistencyError:
        return error_response('Ошибка в базе данных: больше одного пользователя с одинаковым именем пользователя')
    except (DataError, IntegrityError):
        # Можно проверять входные данные, чтобы точно определять ошибку
        return error_response('Ошибка входых данных')

    save_user_to_session(await get_session(request), user)

    return success_response('Вы вошли как {}'.format(user.get('name')))


async def register_user(request) -> Response:
    # todo не пускать пользователя, если он залогинен
    try:
        data = await request.json(loads=json_lib.loads)
    except ValueError:
        return error_response('Ошибка входных данных')

    try:
        user_type = data['user_type']
        name = data['name']
        login = data['login']
        password = data['password']
        password_hash = hashlib.sha256(password.encode()).hexdigest()
    except KeyError:
        return error_response('Недостаточно входных данных')
    except AttributeError:
        return error_response('Ошибка входных данных')

    try:
        user = await create_user(request.app.get('pool_users'), name, user_type, login, password_hash)
    except exceptions.MySQLConnectionNotFound:
        return error_response('Не удалось подключение к базе данных')
        # todo возможно тут переключаться на слейв
    except exceptions.WrongUserType:
        return error_response('Неверно указан user_type')
    except (exceptions.UsernameAlreadyExists, IntegrityError):
        return error_response('Пользователь с таким именем уже зарегистрирован')
    except DataError:
        # Можно проверять входные данные, чтобы точно определять ошибку
        return error_response('Ошибка входых данных')

    save_user_to_session(await get_session(request), user)

    return success_response('Пользователь успешно зарегистрирован')


@login_required()
async def orders_list(request) -> Response:
    try:
        open_orders = await get_open_orders(request.app.get('pool_orders'))
    except exceptions.MySQLConnectionNotFound:
        return error_response('Не удалось подключение к базе данных')
    return success_response(open_orders)


@login_required()
async def users_list(request) -> Response:
    users_type = request.query.get('users_type')
    try:
        users = await get_users(request.app.get('pool_users'), users_type)
    except exceptions.MySQLConnectionNotFound:
        return error_response('Не удалось подключение к базе данных')
    except exceptions.WrongUserType:
        return error_response('Неверно указан user_type')
    return success_response(users)


@login_required('customer')
async def post_order(request) -> Response:
    try:
        data = await request.json(loads=json_lib.loads)
    except ValueError:
        return error_response('Ошибка входных данных')

    try:
        title = data['title']
        value = data['value']
    except KeyError:
        return error_response('Недостаточно входных данных')
    except AttributeError:
        return error_response('Ошибка входных данных')

    session = await get_session(request)
    customer_id = session.get('user_id')        # т.к. в эту вьюху пускают только заказчиков

    try:
        order = await create_order(request.app.get('pool_orders'), title, value, customer_id)
    except exceptions.MySQLConnectionNotFound:
        return error_response('Не удалось подключение к базе данных')
    except exceptions.OrderValueTooSmall:
        return error_response('Сумма заказа слишком мала')
    except ValueError:
        return error_response('Неверное значение суммы заказа')
    except (DataError, IntegrityError, TypeError):
        # Можно проверять входные данные, чтобы точно определять ошибку
        return error_response('Ошибка входых данных')

    return success_response(order)


@login_required()
async def get_order(request) -> Response:
    order_id = request.match_info.get('order_id')

    try:
        order = await find_order(request.app.get('pool_orders'), order_id)
    except exceptions.MySQLConnectionNotFound:
        return error_response('Не удалось подключение к базе данных')

    return success_response(order)


@login_required('executor')
async def update_order(request) -> Response:
    order_id = request.match_info.get('order_id')

    session = await get_session(request)
    try:
        executor_id = int(session.get('user_id'))        # т.к. в эту вьюху пускают только исполнителей
    except ValueError:
        return error_response('Неверное значение id пользователя')

    try:
        order = fulfill_order(request.app.get('pool_orders'),
                              request.app.get('pool_users'),
                              request.app.get('pool_redis_locks'),
                              order_id,
                              executor_id)
    except exceptions.MySQLConnectionNotFound:
        return error_response('Не удалось подключение к базе данных')
    except exceptions.RedisConnectionNotFound:
        return error_response('Не удалось подключение к зранилищу ключ-значение')
    except exceptions.OrderAlreadyClosed:
        return error_response('Заказ уже закрыт')
    except exceptions.OrderProcessed:
        return error_response('Заказ находится в обработке')
    except exceptions.OrderCannotBeFulfilled:
        return error_response('Заказ не может быть выполнен')
    except ValueError:
        return error_response('Ошибка входных данных')
    except exceptions.NotEnoughMoney:
        return error_response('У заказчика недостаточно денег для закрытия заказа')

    return success_response(order)
