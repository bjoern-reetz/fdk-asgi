import os

from asgiref.typing import (
    ASGIApplication,
    Scope,
    ASGIReceiveCallable,
    ASGISendCallable,
    HTTPScope,
    ASGISendEvent,
    HTTPResponseStartEvent,
)
from httptools import parse_url

__version__ = "0.0.1"

FN_HTTP_H_ = b"Fn-Http-H-"
FN_HTTP_Request_Url = b"Fn-Http-Request-Url"
FN_HTTP_Request_Method = b"Fn-Http-Request-Method"
FN_ALLOWED_RESPONSE_CODES = [200, 502, 504]


def map_scope(scope: Scope):
    """Transforms headers etc. sent by Fn/API Gateway so that ASGI apps can understand them."""
    if scope["type"] != "http":
        # do not process anything but HTTPScope's
        return scope

    # see https://asgi.readthedocs.io/en/latest/specs/www.html#http-connection-scope
    scope: HTTPScope

    assert scope["method"] == "POST"
    assert scope["path"] == "/call"

    new_headers = []
    request_url: bytes = b""
    request_method: bytes = b""
    for key, value in scope["headers"]:
        if key.startswith(FN_HTTP_H_):
            new_headers.append((key.removeprefix(FN_HTTP_H_), value))
        elif key == FN_HTTP_Request_Url:
            request_url = value
        elif key == FN_HTTP_Request_Method:
            request_method = value
        else:
            new_headers.append((key, value))

    assert request_url
    assert request_method

    parsed_url = parse_url(request_url)

    scope["method"] = request_method.decode()
    scope["scheme"] = parsed_url.schema.decode()
    scope["path"] = parsed_url.path.decode()
    scope["raw_path"] = parsed_url.path  # byte-string
    scope["query_string"] = parsed_url.query  # byte-string
    scope["root_path"] = os.getenv("FDK_ASGI_ROOT_PATH", "")
    scope["headers"] = new_headers
    # todo: check if scope["client"] is correct
    # todo: check if scope["server"] is correct

    return scope


def wrap_send(send: ASGISendCallable) -> ASGISendCallable:
    async def wrapped_send(message: ASGISendEvent):
        if message["type"] != "http.response.start":
            # only process messages of type=http.response.start
            message: HTTPResponseStartEvent

            new_headers = [
                (key, value)
                if key.lower == b"content-type"
                else (b"Fn-Http-H-" + key, value)
                for key, value in message["headers"]
            ]
            new_headers.append((b"Fn-Http-Status", str(message["status"]).encode()))
            new_headers.append((b"Fn-Fdk-Version", f"fdk-asgi/{__version__}".encode()))

            if message["status"] not in FN_ALLOWED_RESPONSE_CODES:
                message["status"] = 200

        await send(message)

    return wrapped_send


class FnProtocolMiddleware:
    def __init__(self, app: ASGIApplication) -> None:
        self.app = app

    async def __call__(
        self, scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ):
        await self.app(map_scope(scope), receive, wrap_send(send))
