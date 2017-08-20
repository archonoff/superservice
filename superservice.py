from flask import Flask
from flask import jsonify, request, redirect
import pymysql

SYSTEM_COMMISSION = 0.1

app = Flask(__name__)
# todo для ситуации, когда таблицы будут на разных серверах, нужно использовать разные соединения
connection_users = pymysql.connect(host='localhost', user='root', password='1111', db='superservice', charset='utf8', cursorclass=pymysql.cursors.DictCursor)
connection_orders = pymysql.connect(host='localhost', user='root', password='1111', db='superservice', charset='utf8', cursorclass=pymysql.cursors.DictCursor)


# todo запилить логин
# todo запилить сессии и куки


def fulfill_order(order_id, executor_id):
    cursor_orders = connection_orders.cursor()
    cursor_users = connection_users.cursor()
    # todo добавить перевод денег
    # todo уменьшить деньги у заказчика
    # todo увеличить деньги у исполнителя

    # Информация о заказе
    cursor_orders.execute('SELECT * FROM orders WHERE id="{}"'.format(order_id))
    order = cursor_orders.fetchone()
    customer_id = order.get('customer_id')
    order_value = order.get('value')

    # Информация о заказчике
    cursor_users.execute('SELECT * FROM users WHERE id="{}"'.format(customer_id))
    customer = cursor_users.fetchone()
    customer_wallet = customer.get('wallet')

    if order_value > customer_wallet:
        # У заказчика не достаточно денег
        # todo переделать, чтобы денег было недостаточно уже когда размещаешь заказ
        return 'Error: Customer does not have enough amount of money.'

    # Уменьшение денег у заказчика
    cursor_users.execute('UPDATE users SET wallet="{}" WHERE id="{}"'.format(customer_wallet - order_value, customer_id))

    # Информация об исполнителе
    cursor_users.execute('SELECT * FROM users WHERE id="{}"'.format(executor_id))
    executor = cursor_users.fetchone()
    executor_wallet = executor.get('wallet')

    # Увеличение денег у исполнителя
    cursor_users.execute('UPDATE users SET wallet="{}" WHERE id="{}"'.format(executor_wallet + order_value * (1 - SYSTEM_COMMISSION), executor_id))
    # todo можно добавить учет денег системы

    # Заказ отмечается как исполненный
    cursor_orders.execute('UPDATE orders SET fulfilled="1", executor_id="{}" WHERE id="{}";'.format(executor_id, order_id))

    connection_orders.commit()
    connection_users.commit()


def post_order(title, value, customer_id):
    # todo проверка входных параметров, чтобы избежать sql инъекции
    cursor = connection_orders.cursor()
    cursor.execute('INSERT INTO orders (title, value, customer_id) VALUES ("{}", "{}", "{}");'.format(title, value, customer_id))
    connection_orders.commit()


def get_open_orders():
    # fixme почему-то при изменении БД напрямую данные, которые выдает это приложение остаются старыми
    cursor = connection_orders.cursor()
    cursor.execute('SELECT * FROM orders WHERE fulfilled=0;')
    open_orders = cursor.fetchall()
    cursor.close()
    return open_orders


def get_users(users_type=None):
    cursor = connection_users.cursor()
    if users_type:
        if users_type not in ('executor', 'customer'):
            return 'Error: Wrong users type'
        cursor.execute('SELECT * FROM users WHERE type="{}";'.format(users_type))
    else:
        cursor.execute('select * from users;')
    return cursor.fetchall()


@app.route('/dead/')
def dead_func():
    # todo для проверки блокирования выполнения
    while True:
        pass


@app.route('/')
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
    # todo заказчика брить из сессии
    post_order(title=title, value=value, customer_id='6')
    return redirect('/')


@app.route('/orders/<int:order_id>/fulfill/', methods=['PUT'])
def update_order(order_id):
    res = fulfill_order(order_id=order_id, executor_id='4')
    if res:
        return jsonify(res)
    return redirect('/')


@app.route('/users/')
def users_list():
    users_type = request.args.get('users_type')
    users = get_users(users_type)
    return jsonify(users)


if __name__ == '__main__':
    app.run(debug=True)
