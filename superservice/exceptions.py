class MySQLConnectionNotFound(Exception):
    pass


class RedisConnectionNotFound(Exception):
    pass


class UsernameAlreadyExists(Exception):
    pass


class WrongUserType(Exception):
    pass


class WrongLoginOrPassword(Exception):
    pass


class DBConsistencyError(Exception):
    pass


class OrderValueTooSmall(Exception):
    pass
