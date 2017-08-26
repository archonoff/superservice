import hashlib
import pymysql
import os

import settings

from aiohttp import web
from aiohttp.web import json_response, HTTPTemporaryRedirect, Response

from aiohttp_session import SimpleCookieStorage
from aiohttp_session import get_session, setup as setup_session

# from superservice import fulfill_order, post_order, get_open_orders, get_users, create_user     # fixme функции запросов к базе синхронные!


SYSTEM_COMMISSION = 0.1     # Минимальная комиссия - 1%

# для ситуации, когда таблицы будут на разных серверах, нужно использовать разные соединения
connection_users = pymysql.connect(host=settings.MYSQL_HOST,
                                   user=settings.MYSQL_USER,
                                   password=settings.MYSQL_PASSWORD,
                                   db=settings.MYSQL_DB,
                                   charset='utf8',
                                   cursorclass=pymysql.cursors.DictCursor)
connection_orders = pymysql.connect(host=settings.MYSQL_HOST,
                                    user=settings.MYSQL_USER,
                                    password=settings.MYSQL_PASSWORD,
                                    db=settings.MYSQL_DB,
                                    charset='utf8',
                                    cursorclass=pymysql.cursors.DictCursor)


def rest_response(code: str, message) -> Response:
    result_dict = {
        'result': code,
        'message': message,
    }
    return json_response(result_dict)


def success_response(message):
    return rest_response('success', message)


def error_response(message):
    return rest_response('error', message)


# Функции работы с БД

def get_users(users_type=None):
    with connection_users.cursor() as cursor:
        connection_users.commit()      # fixme Это помогло с проблемой необновляющихся запросов
        if users_type:
            if users_type not in ('executor', 'customer'):
                return 'Error: Wrong users type'
            cursor.execute('SELECT * FROM users WHERE type="{}";'.format(users_type))
        else:
            cursor.execute('SELECT * FROM users;')
        users = cursor.fetchall()
    return users


def create_user(name, user_type, username, password_hash):
    # todo нужна проверка username, чтобы избежать инъекций
    if user_type not in ('executor', 'customer'):
        return 'Неверно указан user_type'
    with connection_users.cursor() as cursor:
        cursor.execute('SELECT * FROM users WHERE username="{}"'.format(username))
        users = cursor.fetchall()
        if users:
            return 'Пользователь с таким именем уже зарегистрирован'

        cursor.execute('INSERT INTO users (name, type, username, password) VALUES ("{}", "{}", "{}", "{}");'.format(name, user_type, username, password_hash))
        connection_users.commit()


async def login(request, username, password_hash) -> Response:
    with connection_users.cursor() as cursor:
        cursor.execute('SELECT * FROM users WHERE username="{}" and password="{}"'.format(username, password_hash))
        users: list = cursor.fetchall()
        users_len = len(users)
        if users_len == 0:
            return error_response('Неправильное имя пользователя или пароль')
        elif users_len >= 2:
            return error_response('Ошибка в базе данных: больше одного пользователя')
        else:
            user_id = users[0].get('id')

            session = await get_session(request)
            session['user_id'] = user_id
            session['username'] = username
            return HTTPTemporaryRedirect('/')   # todo rest


def get_open_orders() -> list:
    with connection_orders.cursor() as cursor:
        connection_orders.commit()      # fixme Это помогло с проблемой необновляющихся запросов
        cursor.execute('SELECT * FROM orders WHERE fulfilled=0;')
        open_orders = list(cursor.fetchall())
    return open_orders


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
    return json_response(open_orders)


async def users_list(request) -> Response:
    users_type = request.query.get('users_type')
    users = get_users(users_type)
    return json_response(users)


# Настройка приложения

app = web.Application()
app.router.add_get('/', index)
app.router.add_get('/api/orders/', orders_list)
app.router.add_get('/api/users/', users_list)
app.router.add_post('/api/users/register/', register_user)
app.router.add_post('/api/users/login/', user_login)
# app.router.add_get('/{name}', handle)

setup_session(app, SimpleCookieStorage())


web.run_app(app, host='localhost', port=8000)
