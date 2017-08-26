import os

# todo возможно заюзать для настроек rororo http://rororo.readthedocs.io/en/latest/

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MYSQL_HOST = '127.0.0.1'
MYSQL_PORT = 3306
MYSQL_DB = 'superservice'
MYSQL_USER = ''
MYSQL_PASSWORD = ''

SYSTEM_COMMISSION = 0.1     # Минимальная комиссия - 1%

try:
    from .settings_local import *
except:
    pass