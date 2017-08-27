### Установка зависимостей
`pip install -r requirements.txt`

### Запуск сервера
#### Используя стандартный loop:
`gunicorn -b 0.0.0.0:8000 -w 1 -k aiohttp.GunicornWebWorker superservice.app:app`

#### Используя uvloop (только unix):
`gunicorn -b 0.0.0.0:8000 -w 1 -k aiohttp.GunicornUVLoopWebWorker superservice.app:app`