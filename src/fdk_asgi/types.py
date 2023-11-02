from enum import Enum


class StrEnum(str, Enum):
    def __str__(self):
        return self.value


class HTTPProtocolType(StrEnum):
    auto = "auto"
    h11 = "h11"
    httptools = "httptools"


class LifespanType(StrEnum):
    auto = "auto"
    on = "on"
    off = "off"


class LoopSetupType(StrEnum):
    none = "none"
    auto = "auto"
    asyncio = "asyncio"
    uvloop = "uvloop"


class InterfaceType(StrEnum):
    auto = "auto"
    asgi3 = "asgi3"
    asgi2 = "asgi2"
    # wsgi = "wsgi"  # todo: add WSGI support
