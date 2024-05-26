import typing

from strenum import StrEnum

Scope = typing.MutableMapping[str, typing.Any]
Message = typing.MutableMapping[str, typing.Any]

Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Message], typing.Awaitable[None]]

ASGIApp = typing.Callable[[Scope, Receive, Send], typing.Awaitable[None]]


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
