class ConnectionNotFound(Exception):
    pass


class UsernameAlreadyExists(Exception):
    pass


class WrongUserType(Exception):
    pass


class WrongLoginOrPassword(Exception):
    pass


class DBConsistencyError(Exception):
    pass
