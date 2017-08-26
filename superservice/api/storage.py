from aiohttp.web import Response

from aiohttp_session import get_session

from ..utils import error_response, success_response
from ..exceptions import ConnectionNotFound, WrongUserType, UsernameAlreadyExists


# Функции работы с БД

async def get_users(pool_users, users_type=None):
    if pool_users is None:
        raise ConnectionNotFound()
    async with pool_users.acquire() as conn:
        async with conn.cursor() as cursor:
            if users_type:
                if users_type not in ('executor', 'customer'):
                    raise WrongUserType
                await cursor.execute('SELECT * FROM users WHERE type="{}";'.format(users_type))
            else:
                await cursor.execute('SELECT * FROM users;')
            users = await cursor.fetchall()
    return users


# def get_users_sync(connection_users, connection_orders, users_type=None):
#     with connection_users.cursor() as cursor:
#         connection_users.commit()      # fixme Это помогло с проблемой необновляющихся запросов
#         if users_type:
#             if users_type not in ('executor', 'customer'):
#                 return 'Error: Wrong users type'
#             cursor.execute('SELECT * FROM users WHERE type="{}";'.format(users_type))
#         else:
#             cursor.execute('SELECT * FROM users;')
#         users = cursor.fetchall()
#     return users


def create_user(connection_users, name, user_type, login, password_hash):
    if connection_users is None:
        raise ConnectionNotFound()
    # todo нужна проверка username, чтобы избежать инъекций
    if user_type not in ('executor', 'customer'):
        raise WrongUserType
    with connection_users.cursor() as cursor:
        cursor.execute('SELECT * FROM users WHERE login="{}"'.format(login))
        users = cursor.fetchall()
        if users:
            raise UsernameAlreadyExists

        cursor.execute('INSERT INTO users (name, type, login, password) VALUES ("{}", "{}", "{}", "{}");'.format(name, user_type, login, password_hash))


async def login_user(connection_users, request, username, password_hash) -> Response:
    if connection_users is None:
        raise ConnectionNotFound()
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


async def get_open_orders(pool_orders) -> list:
    if pool_orders is None:
        raise ConnectionNotFound()
    async with pool_orders.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM orders WHERE fulfilled=0;')
            open_orders = list(await cursor.fetchall())
    return open_orders
