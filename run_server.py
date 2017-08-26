from aiohttp import web
from superservice.app import app

web.run_app(app, host='localhost', port=8000)
