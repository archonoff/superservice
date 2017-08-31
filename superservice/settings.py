import os

# todo возможно заюзать для настроек rororo http://rororo.readthedocs.io/en/latest/

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SYSTEM_COMMISSION = 0.1     # Комиссия системы (не должно быть меньше, чем 0.01)

WALLET_MIN_FILLUP = 0.01    # Минимальная сумма для пополнения кошелька (не должно быть меньше, чем 0.01)
WALLET_MAX_VALUE = 1000000  # Максимальная сумма на кошельке

ORDER_MIN_VALUE = 1         # Минимальаня сумма заказа (не должно быть меньше, чем 0.01 / SYSTEM_COMMISSION)
ORDER_MAX_VALUE = 100000    # Максимальная сумма заказа


LOCK_ATTEMPTS_COUNT = 10        # Колисчество попыток повесить лок
LOCK_ATTEMPTS_TIMEOUT = 0.5     # Задержка между попытками обращения
LOCK_EXPIRE_TIMEOUT = 120       # todo рискованная затея


SESSION_DURATION = 86400        # Продолжительность сессии, в секундах


# Хранилища

MYSQL_HOST = '127.0.0.1'
MYSQL_PORT = 3306
MYSQL_DB = 'superservice'
MYSQL_USER = ''
MYSQL_PASSWORD = ''

REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379


try:
    from .settings_local import *
except:
    pass