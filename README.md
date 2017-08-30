### Установка зависимостей
`pip install -r requirements.txt`

### Запуск сервера
```
# Из директории проекта

# Используя стандартный loop:
$ gunicorn -b 0.0.0.0:8000 -w <количество_воркеров> -k aiohttp.GunicornWebWorker superservice.app:app

# Используя uvloop (только *nix системы):
$ gunicorn -b 0.0.0.0:8000 -w <количество_воркеров> -k aiohttp.GunicornUVLoopWebWorker superservice.app:app
```

### TODO
* Предусмотреть переключеие на работу со слейв-сервером MySQL при падении мастера для mysql и redis
* Логгирование
* Все размещенные заказы заказчика
* Все выполненные заказы исполнителя
* Учет денег системы

### API
#### Действия с пользователями

* Список зарегистрированных пользователей (с возможным указанием типа пользователей: только заказчики или только исполнители)
```
URL: /api/users/
Метод: GET
Доступ: только залогиненные пользователи
Параметры запроса:
users_type - тип пользователя: "customer" (заказчик) или "executor" (исполнитель)
```
* Данные о текущем пользователе
```
URL: /api/users/me/
Метод: GET
Доступ: только залогиненные пользователи
```
* Зарегистрировать нового пользователя
```
URL: /api/users/register/
Метод: POST
Доступ: кто угодно
{
    name - имя и фамилия
    user_type - тип пользователя: "customer" (заказчик) или "executor" (исполнитель)
    login - имя пользователя
    password - пароль
}
```
* Вход ранее зарегистрированного пользователя
```
URL: /api/users/login/
Метод: POST
Доступ: кто угодно
{
    login - имя пользователя
    password - пароль
}
```
* Выход из системы
```
URL: /api/users/logout/
Метод: POST
Доступ: только залогиненные пользователи
Тело запроса: любое
```

#### Действия с заказами
* Список открытых заказов
```
URL: /api/orders/
Метод: GET
Доступ: только залогиненные пользователи
```
* Информация о заказе с заданным id
```
URL: /api/orders/<id>/
Метод: GET
Доступ: только залогиненные пользователи
```
* Отметить заказ с заданным id как выполненный
```
URL: /api/orders/<id>/fulfill/
Метод: PUT
Доступ: только исполнители
Тело запроса: любое
```
* Добавить новый заказ
```
URL: /api/orders/add/
Метод: POST
Доступ: только заказчики
Тело запроса:
{
    title - название заказа
    value - сумма заказа
}
```

#### Ответ
```
{
    result - результат запроса: "success" или "error"
    data - данные ответа
}
```
