MYSQL_HOST = '127.0.0.1'
MYSQL_DB = 'superservice'
MYSQL_USER = ''
MYSQL_PASSWORD = ''

try:
    from settings_local import *
except:
    pass