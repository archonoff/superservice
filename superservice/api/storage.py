import asyncio

from aiohttp.web import HTTPNotFound

from .. import settings
from .. import exceptions


# Функции работы с БД

async def get_users(pool_users, users_type=None) -> list:
    if pool_users is None:
        raise exceptions.MySQLConnectionNotFound()
    async with pool_users.acquire() as conn:
        async with conn.cursor() as cursor:
            if users_type:
                if users_type not in ('executor', 'customer'):
                    raise exceptions.WrongUserType
                await cursor.execute('SELECT id, name, type FROM users WHERE type=%s;', (users_type, ))
            else:
                await cursor.execute('SELECT id, name, type FROM users;')
            return await cursor.fetchall()     # todo плохо для большого объема данных


async def create_user(pool_users, name, user_type, login, password_hash) -> dict:
    if pool_users is None:
        raise exceptions.MySQLConnectionNotFound()
    if user_type not in ('executor', 'customer'):
        raise exceptions.WrongUserType
    async with pool_users.acquire() as conn:
        async with conn.cursor() as cursor:
            # Следующая строчка может выкинуть IntegrityError, если пользователь с таким именем уже существует
            await cursor.execute('INSERT INTO users (name, type, login, password) VALUES (%s, %s, %s, %s);', (name, user_type, login, password_hash))

            return {
                'id': cursor.lastrowid,
                'name': name,
                'type': user_type,
                'login': login,
            }


async def check_user(pool_users, login, password_hash) -> dict:
    if pool_users is None:
        raise exceptions.MySQLConnectionNotFound()
    async with pool_users.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM users WHERE login=%s and password=%s', (login, password_hash))
            users: list = await cursor.fetchall()
            users_len = len(users)
            if users_len == 0:
                raise exceptions.WrongLoginOrPassword
            elif users_len >= 2:
                raise exceptions.DBConsistencyError
            else:
                return users[0]


async def get_open_orders(pool_orders) -> list:
    if pool_orders is None:
        raise exceptions.MySQLConnectionNotFound()
    async with pool_orders.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM orders WHERE fulfilled=0;')
            open_orders = await cursor.fetchall()     # todo плохо для большого объема данных
    return open_orders


async def create_order(pool_orders, title, value, customer_id) -> dict:
    if pool_orders is None:
        raise exceptions.MySQLConnectionNotFound()
    value = round(float(value), 2)
    if value < settings.ORDER_MIN_VALUE:
        raise exceptions.OrderValueTooSmall
    async with pool_orders.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('INSERT INTO orders (title, value, customer_id) VALUES (%s, %s, %s);', (title, value, customer_id))

            return {
                'id': cursor.lastrowid,
                'title': title,
                'value': value,
                'customer_id': customer_id,
                'fulfilled': 0,
                'executor_id': None
            }


async def find_order(pool_orders, order_id) -> dict:
    if pool_orders is None:
        raise exceptions.MySQLConnectionNotFound()
    async with pool_orders.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT * FROM orders WHERE id=%s;', (order_id, ))
            order = await cursor.fetchone()

            if order is None:
                raise HTTPNotFound

            return order


async def fulfill_order(pool_orders, pool_users, pool_redis_locks, order_id, executor_id):
    if pool_orders is None:
        raise exceptions.MySQLConnectionNotFound()
    if pool_users is None:
        raise exceptions.MySQLConnectionNotFound()
    if pool_redis_locks is None:
        raise exceptions.RedisConnectionNotFound()

    async with pool_orders.acquire() as conn_orders:
        async with pool_users.acquire() as conn_users:
            async with conn_orders.cursor() as cursor_orders:
                async with conn_users.cursor() as cursor_users:

                    # Лок на заказ
                    for lock_attempt in range(settings.LOCK_ATTEMPTS_COUNT):
                        async with pool_redis_locks.get() as redis:
                            setnx_order_result = await redis.setnx('order:fulfill:{}'.format(order_id), 'lock')

                        if setnx_order_result:
                            # Если успешно установлен лок на заказ
                            await redis.expire('order:fulfill:{}'.format(order_id), settings.LOCK_EXPIRE_TIMEOUT)
                            break

                        await asyncio.sleep(settings.LOCK_ATTEMPTS_TIMEOUT)
                    else:
                        # После всех попыток лок так и не получилось поставить
                        raise exceptions.OrderProcessed()

                    # Информация о заказе
                    await cursor_orders.execute('SELECT * FROM orders WHERE id=%s', (order_id, ))
                    order = await cursor_orders.fetchone()

                    # Проверка, что заказ еще не закрыт
                    fulfilled = order.get('fulfilled')
                    if fulfilled:
                        # Снять лок с заказа
                        async with pool_redis_locks.get() as redis:
                            await redis.delete('order:fulfill:{}'.format(order_id))
                        raise exceptions.OrderAlreadyClosed()

                    customer_id = int(order.get('customer_id'))
                    order_value = float(order.get('value'))

                    # Комиссия системы, округление до сотых
                    commission_value = round(order_value * settings.SYSTEM_COMMISSION, 2)

                    # todo запилить подсчет денег системы

                    # Пробуем сначала повесить лок на юзера с б́ольшим id
                    for lock_attempt in range(settings.LOCK_ATTEMPTS_COUNT):
                        async with pool_redis_locks.get() as redis:
                            setnx_1_result = await redis.setnx('user:fulfill:{}'.format(max(customer_id, executor_id)), 'lock')

                        if setnx_1_result:
                            await redis.expire('user:fulfill:{}'.format(max(customer_id, executor_id)), settings.LOCK_EXPIRE_TIMEOUT)
                            break

                        await asyncio.sleep(settings.LOCK_ATTEMPTS_TIMEOUT)
                    else:
                        # Невозможноть закрытия заказа
                        # Снять лок с заказа
                        async with pool_redis_locks.get() as redis:
                            await redis.delete('order:fulfill:{}'.format(order_id))
                        raise exceptions.OrderCannotBeFulfilled()

                    # Теперь лок на юзера с меньшим id
                    for lock_attempt in range(settings.LOCK_ATTEMPTS_COUNT):
                        async with pool_redis_locks.get() as redis:
                            setnx_2_result = await redis.setnx('user:fulfill:{}'.format(min(customer_id, executor_id)), 'lock')

                        if setnx_2_result:
                            await redis.expire('user:fulfill:{}'.format(min(customer_id, executor_id)), settings.LOCK_EXPIRE_TIMEOUT)
                            break

                        await asyncio.sleep(settings.LOCK_ATTEMPTS_TIMEOUT)
                    else:
                        # Невозможноть закрытия заказа
                        # Снять лок с заказа и с первого юзера
                        async with pool_redis_locks.get() as redis:
                            await redis.delete('order:fulfill:{}'.format(order_id))
                            await redis.delete('user:fulfill:{}'.format(max(customer_id, executor_id)))
                        raise exceptions.OrderCannotBeFulfilled()

                    # Теперь лок стоит на заказе и обоих пользователях, можно переводить деньги

                    # Информация о заказчике
                    await cursor_users.execute('SELECT * FROM users WHERE id=%s', (customer_id, ))
                    customer = await cursor_users.fetchone()
                    customer_wallet = float(customer.get('wallet'))

                    if order_value > customer_wallet:
                        # У заказчика недостаточно денег
                        # Снять лок с заказа и с обоих юзеров
                        async with pool_redis_locks.get() as redis:
                            await redis.delete('order:fulfill:{}'.format(order_id))
                            await redis.delete('user:fulfill:{}'.format(max(customer_id, executor_id)))
                            await redis.delete('user:fulfill:{}'.format(min(customer_id, executor_id)))
                        raise exceptions.NotEnoughMoney()

                    # Информация об исполнителе
                    await cursor_users.execute('SELECT * FROM users WHERE id=%s', (executor_id, ))
                    executor = await cursor_users.fetchone()
                    executor_wallet = executor.get('wallet')

                    # Уменьшение денег у заказчика
                    await cursor_users.execute('UPDATE users SET wallet=%s WHERE id=%s', (customer_wallet - order_value, customer_id))

                    # Увеличение денег у исполнителя
                    await cursor_users.execute('UPDATE users SET wallet=%s WHERE id=%s', (executor_wallet + order_value - commission_value, executor_id))

                    # Заказ отмечается как исполненный
                    await cursor_orders.execute('UPDATE orders SET fulfilled="1", executor_id=%s WHERE id=%s;', (executor_id, order_id))
                    order['fulfilled'] = 1
                    order['executor_id'] = executor_id

                    # Снять лок с заказа и с обоих юзеров
                    async with pool_redis_locks.get() as redis:
                        await redis.delete('order:fulfill:{}'.format(order_id))
                        await redis.delete('user:fulfill:{}'.format(max(customer_id, executor_id)))
                        await redis.delete('user:fulfill:{}'.format(min(customer_id, executor_id)))

                    return order


async def get_user(pool_users, user_id):
    if pool_users is None:
        raise exceptions.MySQLConnectionNotFound()
    async with pool_users.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute('SELECT id, name, type, wallet FROM users WHERE id=%s;', (user_id, ))
            user = await cursor.fetchone()

            if user is None:
                raise HTTPNotFound

            return user
