from flask import Flask
from flask import jsonify, request, redirect, Response
import pymysql

SYSTEM_COMMISSION = 0.1     # Минимальная комиссия - 1%

app = Flask(__name__)
# для ситуации, когда таблицы будут на разных серверах, нужно использовать разные соединения
connection_users = pymysql.connect(host='localhost', user='root', password='1111', db='superservice', charset='utf8', cursorclass=pymysql.cursors.SSDictCursor)
connection_orders = pymysql.connect(host='localhost', user='root', password='1111', db='superservice', charset='utf8', cursorclass=pymysql.cursors.SSDictCursor)


# todo запилить логин
# todo запилить сессии и куки


def fulfill_order(order_id, executor_id):
    cursor_orders = connection_orders.cursor()
    cursor_users = connection_users.cursor()

    # todo получить уникальный доступ к нужным строчкам базы, поставив на них лок

    # Информация о заказе и заказчике
    cursor_orders.execute('SELECT * FROM orders WHERE id="{}"'.format(order_id))
    order = cursor_orders.fetchone()
    customer_id = order.get('customer_id')
    order_value = order.get('value')
    commission_value = order_value * SYSTEM_COMMISSION

    # Информация о заказчике
    cursor_users.execute('SELECT * FROM users WHERE id="{}"'.format(customer_id))
    customer = cursor_users.fetchone()
    customer_wallet = customer.get('wallet')

    if order_value > customer_wallet:
        # У заказчика не достаточно денег
        return 'Error: Customer does not have enough amount of money.'

    # Уменьшение денег у заказчика
    cursor_users.execute('UPDATE users SET wallet="{}" WHERE id="{}"'.format(customer_wallet - order_value, customer_id))

    # Информация об исполнителе
    cursor_users.execute('SELECT * FROM users WHERE id="{}"'.format(executor_id))
    executor = cursor_users.fetchone()
    executor_wallet = executor.get('wallet')

    # Увеличение денег у исполнителя
    cursor_users.execute('UPDATE users SET wallet="{}" WHERE id="{}"'.format(executor_wallet + order_value - commission_value, executor_id))

    # Заказ отмечается как исполненный
    cursor_orders.execute('UPDATE orders SET fulfilled="1", executor_id="{}" WHERE id="{}";'.format(executor_id, order_id))

    # todo добавить учет денег системы

    connection_orders.commit()
    connection_users.commit()


def post_order(title, value, customer_id):
    # todo проверка входных параметров, чтобы избежать sql инъекции
    # Минимальаня сумма заказа - 1 (рубль)
    if value < 1:
        return 'Error: Minimal order value equals 1.'
    with connection_orders.cursor() as cursor:
        cursor.execute('INSERT INTO orders (title, value, customer_id) VALUES ("{}", "{}", "{}");'.format(title, value, customer_id))
        connection_orders.commit()


def get_open_orders():
    with connection_orders.cursor() as cursor:
        connection_orders.commit()      # Это помогло с проблемой необновляющихся запросов
        cursor.execute('SELECT * FROM orders WHERE fulfilled=0;')
        open_orders = list(cursor.fetchall_unbuffered())
    return open_orders


def get_users(users_type=None):
    with connection_users.cursor() as cursor:
        connection_users.commit()      # Это помогло с проблемой необновляющихся запросов
        if users_type:
            if users_type not in ('executor', 'customer'):
                return 'Error: Wrong users type'
            cursor.execute('SELECT * FROM users WHERE type="{}";'.format(users_type))
        else:
            cursor.execute('SELECT * FROM users;')
        users = cursor.fetchall()
    return users


def create_user(name, user_type):
    if user_type not in ('executor', 'customer'):
        return 'Error: Wrong user type'
    # todo нужна проверка name, чтобы избежать инъекций
    # todo Добавить создание пароля
    with connection_users.cursor() as cursor:
        cursor.execute('INSERT INTO users (name, type) VALUES ("{}", "{}");'.format(name, user_type))
        connection_users.commit()


@app.route('/dead/')
def dead_func():
    # todo для проверки блокирования выполнения
    while True:
        pass


@app.route('/', methods=['GET'])
def index():
    return redirect('/orders/')


@app.route('/orders/', methods=['GET'])
def orders_list():
    open_orders = get_open_orders()
    return jsonify(open_orders)


@app.route('/orders/', methods=['POST'])
def add_order():
    title = request.args.get('title')
    value = request.args.get('value')
    # todo заказчика брать из сессии
    res = post_order(title=title, value=value, customer_id='6')
    if res:
        return jsonify(res)
    return redirect('/')


@app.route('/orders/<int:order_id>/fulfill/', methods=['PUT'])
def update_order(order_id):
    res = fulfill_order(order_id=order_id, executor_id='4')
    if res:
        return jsonify(res)
    return redirect('/')


@app.route('/users/', methods=['GET'])
def users_list():
    users_type = request.args.get('users_type')
    users = get_users(users_type)
    return jsonify(users)


@app.route('/dummy/', methods=['GET'])
def dummy():
    return Response(response='dummy')


@app.route('/users/add/', methods=['POST'])
def add_user():
    user_type = request.args.get('user_type')
    name = request.args.get('name')
    res = create_user(name=name, user_type=user_type)
    if res:
        return jsonify(res)
    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)#, debug=True)
