from aiohttp.web import Response

from aiohttp_session import get_session

from ..app import pool_users, connection_orders, connection_users
from ..utils import error_response, success_response


# Функции работы с БД

async def get_users(users_type=None):
    async with pool_users.acquire() as conn:
        async with conn.cursor() as cursor:
            # connection_users.commit()      # fixme Это помогло с проблемой необновляющихся запросов
            if users_type:
                if users_type not in ('executor', 'customer'):
                    return 'Error: Wrong users type'        # todo
                await cursor.execute('SELECT * FROM users WHERE type="{}";'.format(users_type))
            else:
                await cursor.execute('SELECT * FROM users;')
            users = await cursor.fetchall()
    return users


def get_users_sync(users_type=None):
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
            name = users[0].get('name')

            session = await get_session(request)
            session['user_id'] = user_id
            session['username'] = username
            return success_response('Вы вошли как {}'.format(name))


def get_open_orders() -> list:
    with connection_orders.cursor() as cursor:
        connection_orders.commit()      # fixme Это помогло с проблемой необновляющихся запросов
        cursor.execute('SELECT * FROM orders WHERE fulfilled=0;')
        open_orders = list(cursor.fetchall())
    return open_orders
