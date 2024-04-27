from requests import Session
from . import users
from . import translations


def create_session() -> Session:
    global __factory
    return __factory()
