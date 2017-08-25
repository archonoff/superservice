from aiohttp import web
from superservice import fulfill_order, post_order, get_open_orders, get_users, create_user     # fixme функции запросов к базе синхронные!


async def index(request):
    return web.HTTPTemporaryRedirect('/orders/')


async def orders_list(request):
    open_orders = get_open_orders()
    return web.json_response(open_orders)


app = web.Application()
app.router.add_get('/', index)
app.router.add_get('/orders/', orders_list)
# app.router.add_get('/{name}', handle)

web.run_app(app, host='localhost', port=8000)
