from ..exceptions import MySQLConnectionNotFound, WrongUserType, UsernameAlreadyExists, WrongLoginOrPassword, DBConsistencyError, RedisConnectionNotFound


# Функции работы с БД

async def get_users(pool_users, users_type=None) -> list:
    if pool_users is None:
        raise MySQLConnectionNotFound()
    async with pool_users.acquire() as conn:
        async with conn.cursor() as cursor:
            if users_type:
                if users_type not in ('executor', 'customer'):
                    raise WrongUserType
                await cursor.execute('SELECT * FROM users WHERE type=%s;', (users_type, ))
            else:
                await cursor.execute('SELECT * FROM users;')
            return await cursor.fetchall()     # todo возможно fetchall не лучший вариант


async def create_user(pool_users, name, user_type, login, password_hash) -> dict:
    if pool_users is None:
        raise MySQLConnectionNotFound()
    if user_type not in ('executor', 'customer'):
        raise WrongUserType
    async with pool_users.acquire() as conn:
        async with conn.cursor() as cursor:
            # Следующая строчка может выкинуть IntegrityError
            await cursor.execute('INSERT INTO users (name, type, login, password) VALUES (%s, %s, %s, %s);', (name, user_type, login, password_hash))

            return {
                'id': cursor.lastrowid,
                'name': name,
                'user_type': user_type,
                'login': login,
            }


async def check_user(pool_users, login, password_hash) -> dict:
    if pool_users is None:
        raise MySQLConnectionNotFound()
    async with pool_users.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM users WHERE login=%s and password=%s', (login, password_hash))
            users: list = await cursor.fetchall()
            users_len = len(users)
            if users_len == 0:
                raise WrongLoginOrPassword
            elif users_len >= 2:
                raise DBConsistencyError
            else:
                return users[0]


async def get_open_orders(pool_orders) -> list:
    if pool_orders is None:
        raise MySQLConnectionNotFound()
    async with pool_orders.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM orders WHERE fulfilled=0;')
            open_orders = await cursor.fetchall()     # todo возможно fetchall - не лучший вариант
    return open_orders
