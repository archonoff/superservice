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


class OrderAlreadyClosed(Exception):
    pass


class OrderProcessed(Exception):
    pass


class OrderCannotBeFulfilled(Exception):
    pass


class NotEnoughMoney(Exception):
    pass


class WalletCannotBeFilledUp(Exception):
    pass


class WalletValueTooBig(Exception):
    pass
