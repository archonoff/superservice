### Установка зависимостей
`pip install -r requirements.txt`

### Запуск сервера
Из директории проекта

#### Используя стандартный loop:
`gunicorn -b 0.0.0.0:8000 -w 1 -k aiohttp.GunicornWebWorker superservice.app:app`

#### Используя uvloop (только *nix системы):
`gunicorn -b 0.0.0.0:8000 -w 1 -k aiohttp.GunicornUVLoopWebWorker superservice.app:app`

#### TODO
* Предусмотреть переключеие на работу со слейв-сервером MySQL при падении мастера
* Предусмотреть переключеие на работу со слейв-сервером Redis при падении мастера
* Нормальный фронт
