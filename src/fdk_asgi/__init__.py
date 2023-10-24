import logging
import os
from importlib.metadata import version

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
from starlette import status
from starlette.responses import Response

FN_FDK_VERSION_HEADER = (b"Fn-Fdk-Version", f"fdk-asgi/{version(__name__)}".encode())
FN_HTTP_H_ = b"fn-http-h-"
FN_HTTP_REQUEST_URL = b"fn-http-request-url"
FN_HTTP_REQUEST_METHOD = b"fn-http-request-method"
FN_ALLOWED_RESPONSE_CODES = [
    status.HTTP_200_OK,
    status.HTTP_502_BAD_GATEWAY,
    status.HTTP_504_GATEWAY_TIMEOUT,
]


logger = logging.getLogger(__name__)


def map_scope(scope: Scope):
    """Transforms headers etc. sent by Fn/API Gateway so that ASGI apps can understand them."""

    # do not process anything but HTTPScope's
    if scope["type"] != "http":
        return scope

    # see https://asgi.readthedocs.io/en/latest/specs/www.html#http-connection-scope
    scope: HTTPScope

    # todo: replace these assertions with proper routes with error responses etc.
    assert scope["method"] == "POST"
    assert scope["path"] == "/call"

    http_headers = []
    request_url: bytes = b""
    request_method: bytes = b""
    for key, value in scope["headers"]:
        if key.startswith(FN_HTTP_H_):
            http_headers.append((key.removeprefix(FN_HTTP_H_), value))
        elif key == FN_HTTP_REQUEST_URL:
            request_url = value
        elif key == FN_HTTP_REQUEST_METHOD:
            request_method = value
        else:
            http_headers.append((key, value))

    assert request_url
    assert request_method

    parsed_url = parse_url(request_url)

    scope["method"] = request_method.decode()
    scope["scheme"] = parsed_url.schema.decode()
    scope["path"] = parsed_url.path.decode()
    scope["raw_path"] = parsed_url.path  # byte-string
    scope["query_string"] = parsed_url.query  # byte-string
    scope["root_path"] = os.getenv("FDK_ASGI_ROOT_PATH", "")
    scope["headers"] = http_headers
    # todo: check if scope["client"] is correct
    # todo: check if scope["server"] is correct

    return scope


def wrap_send(send: ASGISendCallable) -> ASGISendCallable:
    async def wrapped_send(message: ASGISendEvent):
        # only process messages of type=http.response.start,
        # leave message of other types untouched
        if message["type"] == "http.response.start":
            message: HTTPResponseStartEvent

            new_headers = [
                (key, value)
                if key.lower == b"content-type"
                else (FN_HTTP_H_ + key, value)
                for key, value in message["headers"]
            ]
            new_headers.append((b"Fn-Http-Status", str(message["status"]).encode()))
            new_headers.append(FN_FDK_VERSION_HEADER)

            message["headers"] = new_headers

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
        if scope["type"] == "http":
            if scope["path"] != "/call":
                await Response(status_code=status.HTTP_404_NOT_FOUND)(
                    scope, receive, send
                )
                return
            if scope["method"] != "POST":
                await Response(status_code=status.HTTP_405_METHOD_NOT_ALLOWED)(
                    scope, receive, send
                )
                return
        await self.app(map_scope(scope), receive, wrap_send(send))
