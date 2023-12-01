from __future__ import annotations

import logging
from http import HTTPStatus
from importlib.metadata import version

from asgiref.typing import (
    ASGIReceiveCallable,
    ASGISendCallable,
    HTTPResponseStartEvent,
    HTTPScope,
)
from httptools import parse_url

from fdk_asgi.exceptions import (
    FnMiddlewareError,
    MethodNotAllowedError,
    MissingMethodError,
    MissingUrlError,
    PathNotFoundError,
)
from fdk_asgi.types import ASGIApp, Message, Send
from fdk_asgi.utils import get_client_addr, get_path_with_query_string

FN_FDK_VERSION_HEADER = (
    b"fn-fdk-version",
    f"fdk-asgi/{version(__package__)}".encode(),
)

FN_HTTP_H_ = b"fn-http-h-"
FN_HTTP_REQUEST_URL = b"fn-http-request-url"
FN_HTTP_REQUEST_METHOD = b"fn-http-method"
FN_HTTP_STATUS = b"fn-http-status"
FN_ALLOWED_RESPONSE_CODES = [
    HTTPStatus.OK,
    HTTPStatus.BAD_GATEWAY,
    HTTPStatus.GATEWAY_TIMEOUT,
]

logger = logging.getLogger(__name__)
logger_access = logging.getLogger(f"{__package__}.access")


class FnMiddleware:
    """A pure ASGI middleware, wrapping a regular ASGI application
    and translating Fn <-> REST."""

    def __init__(self, app: ASGIApp, prefix: str = ""):
        self.app = app
        self.prefix = prefix

    async def __call__(
        self, scope: HTTPScope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ):
        try:
            mapped_scope = self._map_scope(scope)
        except FnMiddlewareError as exception:
            logger.critical(exception)
            await send(
                {
                    "type": "http.response.start",
                    "status": exception.code,
                    "headers": [
                        [b"content-type", b"text/plain"],
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": str(exception).encode(),
                }
            )
            return
        await self.app(mapped_scope, receive, self._wrap_send(send, scope))

    def _map_scope(self, scope: HTTPScope) -> HTTPScope:
        """Transforms headers etc. sent by Fn/API Gateway
        so that ASGI apps can understand them."""

        # see https://asgi.readthedocs.io/en/latest/specs/www.html#http-connection-scope

        if scope["path"] != "/call":
            raise PathNotFoundError()
        if scope["method"] != "POST":
            raise MethodNotAllowedError()

        http_headers = []
        request_url: bytes | None = None
        request_method: bytes | None = None
        for key, value in scope["headers"]:
            key_lower = key.lower()
            if key_lower.startswith(FN_HTTP_H_):
                http_headers.append((key[len(FN_HTTP_H_) :], value))
            elif key_lower == FN_HTTP_REQUEST_URL:
                request_url = value
            elif key_lower == FN_HTTP_REQUEST_METHOD:
                request_method = value
            else:
                http_headers.append((key, value))

        try:
            parsed_url = parse_url(request_url)
        except TypeError:
            raise MissingUrlError()

        if request_method is None:
            raise MissingMethodError()

        scope["method"] = request_method.decode()
        scope["path"] = parsed_url.path.decode().removeprefix(self.prefix)
        scope["raw_path"] = parsed_url.path  # byte-string, excluding any query string
        scope["query_string"] = parsed_url.query or b""  # byte-string
        # scope has precedence over environment variable
        scope["root_path"] = self.prefix
        scope["headers"] = http_headers

        return scope

    @staticmethod
    def _wrap_send(send: ASGISendCallable, scope: HTTPScope) -> Send:
        async def wrapped_send(message: Message):
            # only process messages of type=http.response.start,
            # leave message of other types untouched
            if message["type"] == "http.response.start":
                message: HTTPResponseStartEvent

                new_headers = [
                    (key, value)
                    if key.lower() == b"content-type"
                    else (FN_HTTP_H_ + key, value)
                    for key, value in message["headers"]
                ]
                new_headers.append((FN_HTTP_STATUS, str(message["status"]).encode()))
                new_headers.append(FN_FDK_VERSION_HEADER)

                message["headers"] = new_headers

                original_status_code = message["status"]
                if message["status"] not in FN_ALLOWED_RESPONSE_CODES:
                    message["status"] = HTTPStatus.OK

                logger_access.info(
                    '%s - "%s %s HTTP/%s" %d',
                    get_client_addr(scope),
                    scope["method"],
                    get_path_with_query_string(scope),
                    scope["http_version"],
                    original_status_code,
                )

            await send(message)

        return wrapped_send
