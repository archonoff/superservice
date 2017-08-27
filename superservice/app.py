import asyncio
import aiomysql
import aioredis

from aiohttp import web

from aiohttp_session import SimpleCookieStorage
from aiohttp_session import setup as setup_session

from . import settings
from .api import views


# Настройка приложения

# try:
#     import uvloop
#     asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())     # fixme на маке стало хуже        # todo не нужно, если запускать гуникорном
# except:
#     pass

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
# Путы подключения к мусклу
# Если таблицы находятся на разных серверах - указать соответсвующие настройки
pool_orders = loop.run_until_complete(aiomysql.create_pool(host=settings.MYSQL_HOST,
                                                           port=settings.MYSQL_PORT,
                                                           user=settings.MYSQL_USER,
                                                           password=settings.MYSQL_PASSWORD,
                                                           db=settings.MYSQL_DB,
                                                           **shared_mysql_settings))

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

app = web.Application(loop=loop)
app.router.add_get('/', views.index)
app.router.add_get('/dummy/', views.dummy)
app.router.add_get('/api/orders/', views.orders_list)
app.router.add_post('/api/orders/create/', views.post_order)

app.router.add_get('/api/users/', views.users_list)
app.router.add_post('/api/users/register/', views.register_user)
app.router.add_post('/api/users/login/', views.login_user)
# app.router.add_get('/{name}', handle)     # todo для примера

setup_session(app, SimpleCookieStorage())

app['pool_users'] = pool_users
app['pool_orders'] = pool_orders

app['pool_redis_locks'] = pool_redis_locks
app['pool_redis_sessions'] = pool_redis_sessions
