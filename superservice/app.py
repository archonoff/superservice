import asyncio
import uvloop
import pymysql
import aiomysql

from aiohttp import web

from aiohttp_session import SimpleCookieStorage
from aiohttp_session import setup as setup_session

from . import settings
from .api import views


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




# Настройка приложения

# asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())     # fixme на маке стало хуже        # todo не нужно, если запускать гуникорном
loop = asyncio.get_event_loop()

app = web.Application(loop=loop)
app.router.add_get('/', views.index)
app.router.add_get('/dummy/', views.dummy)
app.router.add_get('/api/orders/', views.orders_list)
app.router.add_get('/api/users/', views.users_list)
app.router.add_post('/api/users/register/', views.register_user)
app.router.add_post('/api/users/login/', views.user_login)
# app.router.add_get('/{name}', handle)     # todo для примера

setup_session(app, SimpleCookieStorage())


pool_users = loop.run_until_complete(aiomysql.create_pool(host=settings.MYSQL_HOST,
                                                          port=settings.MYSQL_PORT,
                                                          user=settings.MYSQL_USER,
                                                          password=settings.MYSQL_PASSWORD,
                                                          db=settings.MYSQL_DB,
                                                          loop=loop,
                                                          maxsize=50,
                                                          minsize=10))


# web.run_app(app, host='localhost', port=8000)     # todo не нужно, если запускать гуникорном
