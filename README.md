### Установка зависимостей
```
# Необходим Python 3.6
$ pip install -r requirements.txt
```

### Запуск сервера
```
# Из директории проекта

# Используя стандартный loop:
$ gunicorn -b 0.0.0.0:8000 -w <количество_воркеров> -k aiohttp.GunicornWebWorker superservice.app:app

# Используя uvloop (только *nix системы):
$ gunicorn -b 0.0.0.0:8000 -w <количество_воркеров> -k aiohttp.GunicornUVLoopWebWorker superservice.app:app
```

### Что не сделано (тупо не хватило времени)
* Переключеие на работу со слейв-сервером MySQL при падении мастера для mysql и redis
* Логгирование
* Все размещенные заказы заказчика
* Все выполненные заказы исполнителя
* Учет денег системы (nosql хранилище на диске)
* Возможно сделать хранение всех сумм целочисленными значениями "копеек", а не "рублей" с плавающей точкой

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
Тело запроса (json):
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
Тело запроса (json):
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
* Пополнение кошелька
```
URL: /api/users/me/wallet/
Метод: PUT
Доступ: только заказчики
Тело запроса (json):
{
    value - сумма пополнения кошелька
}
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
Тело запроса (json):
{
    title - название заказа
    value - сумма заказа
}
```

#### Ответ (json)
```
{
    result - результат запроса: "success" или "error"
    data - данные ответа
}
```
