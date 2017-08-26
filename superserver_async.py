import hashlib
import pymysql

import settings

from aiohttp import web
from aiohttp.web import json_response, HTTPTemporaryRedirect

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


def error_response(error_message):
    result_dict = {
        'result': 'error',
        'message': error_message,
    }
    return json_response(result_dict)


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


def get_open_orders():
    with connection_orders.cursor() as cursor:
        connection_orders.commit()      # fixme Это помогло с проблемой необновляющихся запросов
        cursor.execute('SELECT * FROM orders WHERE fulfilled=0;')
        open_orders = list(cursor.fetchall())
    return open_orders


# Хэндлеры

async def index(request):
    return HTTPTemporaryRedirect('/orders/')


async def login(request, username, password_hash):
    result, user_id, username = True, '112', 'sdf'      # todo проверить с данными из БД на совпадение

    if result:
        session = await get_session(request)
        session['user_id'] = user_id
        session['username'] = username
        return HTTPTemporaryRedirect('/')
    else:
        return error_response('Неправильное имя пользователя или пароль')


async def user_login(request):
    data = await request.json()
    username = data.get('username')
    password = data.get('password')
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    return login(request, username, password_hash)


async def register_user(request):
    data = await request.json()
    user_type = data.get('user_type')
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    # res = create_user(name=name, user_type=user_type, username=username, password=password_hash)
    # todo обработка результатов регистрации
    res = None
    if res:
        return json_response(res)

    # todo залогиниться под новым пользователем
    return login(request, username, password_hash)


async def orders_list(request):
    open_orders = get_open_orders()
    return json_response(open_orders)


async def users_list(request):
    users_type = request.query.get('users_type')
    users = get_users(users_type)
    return json_response(users)


async def vue(request):
    with open(settings.BASE_DIR + '/frontend/index.html', 'r') as f:
        html = f.read()
    return web.Response(body=html, content_type='text/html', charset='utf-8')


# Настройка приложения

app = web.Application()
app.router.add_get('/', index)
app.router.add_get('/vue/', vue)
app.router.add_get('/orders/', orders_list)
app.router.add_post('/users/', users_list)
app.router.add_post('/users/register/', register_user)
app.router.add_post('/users/login/', user_login)
# app.router.add_get('/{name}', handle)

setup_session(app, SimpleCookieStorage())


web.run_app(app, host='localhost', port=8000)
