import asyncio
import aiomysql
import aioredis

from aiohttp import web

from aiohttp_session.redis_storage import RedisStorage
from aiohttp_session import setup as setup_session

from . import settings
from .api import views


loop = asyncio.get_event_loop()

shared_mysql_settings = {
    'charset': 'utf8',
    'cursorclass': aiomysql.cursors.DictCursor,
    'autocommit': True,
    'loop': loop,
    'minsize': 5,
    'maxsize': 50,
}

# todo предусмотреть переключение на слейва при недоступности мастера
# Пулы подключения к мусклу
# Если таблицы находятся на разных серверах - указать соответсвующие настройки
# Для таблицы orders
pool_orders = loop.run_until_complete(aiomysql.create_pool(host=settings.MYSQL_HOST,
                                                           port=settings.MYSQL_PORT,
                                                           user=settings.MYSQL_USER,
                                                           password=settings.MYSQL_PASSWORD,
                                                           db=settings.MYSQL_DB,
                                                           **shared_mysql_settings))

# Для таблицы users
pool_users = loop.run_until_complete(aiomysql.create_pool(host=settings.MYSQL_HOST,
                                                          port=settings.MYSQL_PORT,
                                                          user=settings.MYSQL_USER,
                                                          password=settings.MYSQL_PASSWORD,
                                                          db=settings.MYSQL_DB,
                                                          **shared_mysql_settings))

# Пулы подключения к редису
pool_redis_locks = loop.run_until_complete(aioredis.create_pool((settings.REDIS_HOST, settings.REDIS_PORT),
                                                                db=0,
                                                                loop=loop,
                                                                minsize=5,
                                                                maxsize=50))

pool_redis_sessions = loop.run_until_complete(aioredis.create_pool((settings.REDIS_HOST, settings.REDIS_PORT),
                                                                   db=1,
                                                                   loop=loop,
                                                                   minsize=5,
                                                                   maxsize=50))

# todo запилить логгирование (ошибки + действия пользователй)
app = web.Application(loop=loop)
app.router.add_get('/', views.index)
app.router.add_get('/api/orders/', views.orders_list)
app.router.add_post('/api/orders/add/', views.post_order)
app.router.add_get(r'/api/orders/{order_id:\d+}/', views.get_order)
app.router.add_put(r'/api/orders/{order_id:\d+}/fulfill/', views.update_order)

app.router.add_get('/api/users/', views.users_list)
app.router.add_get('/api/users/me/', views.users_me)
app.router.add_post('/api/users/register/', views.register_user)
app.router.add_post('/api/users/login/', views.login_user)
app.router.add_post('/api/users/logout/', views.logout_user)

setup_session(app, RedisStorage(redis_pool=pool_redis_sessions,
                                cookie_name='SUPERSERVICE_SESSION',
                                max_age=settings.SESSION_DURATION))

app['pool_users'] = pool_users
app['pool_orders'] = pool_orders

app['pool_redis_locks'] = pool_redis_locks
