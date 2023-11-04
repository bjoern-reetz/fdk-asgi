from __future__ import annotations

import logging
import os
import typing
from importlib.metadata import version

from asgiref.typing import (
    ASGIApplication,
    ASGIReceiveCallable,
    ASGISendCallable,
    ASGISendEvent,
    HTTPResponseStartEvent,
    HTTPScope,
)
from httptools import parse_url
from starlette import status
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route
from starlette.types import ASGIApp, Lifespan

FN_FDK_VERSION_HEADER = (
    b"Fn-Fdk-Version",
    f"fdk-asgi/{version(__package__)}".encode(),
)
FN_HTTP_H_ = b"fn-http-h-"
FN_HTTP_REQUEST_URL = b"fn-http-request-url"
FN_HTTP_REQUEST_METHOD = b"fn-http-request-method"
FN_ALLOWED_RESPONSE_CODES = [
    status.HTTP_200_OK,
    status.HTTP_502_BAD_GATEWAY,
    status.HTTP_504_GATEWAY_TIMEOUT,
]
logger = logging.getLogger(__name__)


class FnApplication(Starlette):
    """A wrapper around Starlette that ensures some settings conform
    to the Fn container contract."""

    def __init__(
        self,
        app: ASGIApplication | ASGIApp,
        debug: bool = False,
        middleware: typing.Sequence[Middleware] | None = None,
        exception_handlers: any = None,  # todo: add type annotation
        on_startup: typing.Sequence[typing.Callable[[], typing.Any]] | None = None,
        on_shutdown: typing.Sequence[typing.Callable[[], typing.Any]] | None = None,
        lifespan: Lifespan[ASGIApplication] | None = None,
    ):
        self.app = app

        super().__init__(
            debug,
            [
                Route(
                    "/call",
                    endpoint=FnMiddleware(app),
                    methods=["POST"],
                )
            ],
            middleware,
            exception_handlers,
            on_startup,
            on_shutdown,
            lifespan,
        )


class FnMiddleware:
    """A pure ASGI middleware, wrapping a regular ASGI application
    and translating Fn <-> REST."""

    def __init__(self, app: ASGIApplication | ASGIApp):
        self.app = app

    async def __call__(
        self, scope: HTTPScope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ):
        logger.debug(f"{scope=}")
        mapped_scope = self.map_scope(scope)
        logger.debug(f"{mapped_scope=}")
        await self.app(mapped_scope, receive, self.wrap_send(send))

    @staticmethod
    def map_scope(scope: HTTPScope) -> HTTPScope:
        """Transforms headers etc. sent by Fn/API Gateway
        so that ASGI apps can understand them."""

        # see https://asgi.readthedocs.io/en/latest/specs/www.html#http-connection-scope

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

    @staticmethod
    def wrap_send(send: ASGISendCallable) -> ASGISendCallable:
        async def wrapped_send(message: ASGISendEvent):
            logger.debug(f"{message=}")

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
                new_headers.append((b"Fn-Http-Status", str(message["status"]).encode()))
                new_headers.append(FN_FDK_VERSION_HEADER)

                message["headers"] = new_headers

                if message["status"] not in FN_ALLOWED_RESPONSE_CODES:
                    message["status"] = status.HTTP_200_OK

            logger.debug(f"transformed_message={message}")
            await send(message)

        return wrapped_send
