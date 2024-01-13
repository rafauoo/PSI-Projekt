import enum

class MsgType(enum.Enum):
    REQUEST = 1
    RESPONSE = 2
    INIT = 3
    CONN_CLOSE_CLIENT = 4
    CONN_CLOSE_SERVER = 5