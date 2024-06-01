import typing
from string import printable

import fdk_asgi.types
from fdk_asgi.app import (
    FN_ALLOWED_RESPONSE_CODES,
    FN_HTTP_H_,
    FN_HTTP_REQUEST_METHOD,
    FN_HTTP_REQUEST_URL,
    FN_HTTP_STATUS,
)
from httptools import parse_url
from httpx import Headers
from hypothesis import strategies as st
from strenum import StrEnum


def st_json(*, max_leaves: int = 5) -> st.SearchStrategy:
    return st.recursive(
        st.none()
        | st.booleans()
        | st.floats(allow_nan=False, allow_infinity=False, allow_subnormal=False)
        | st.text(printable),
        lambda children: st.lists(children)
        | st.dictionaries(st.text(printable), children),
        max_leaves=max_leaves,
    )


class HTTPMethod(StrEnum):
    GET = "GET"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    CONNECT = "CONNECT"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    PATCH = "PATCH"


class InverseFnMiddleware:
    def __init__(
        self, app: fdk_asgi.types.ASGIApp, *, url_prefix: str = "http://testclient"
    ):
        self.app = app
        self.url_prefix = url_prefix.rstrip("/").encode()

    def _construct_request_url(self, scope: fdk_asgi.types.Scope) -> bytes:
        raw_path = scope["raw_path"] or parse_url(scope["path"].encode()).path
        return typing.cast(bytes, self.url_prefix + raw_path + scope["query_string"])

    async def __call__(
        self,
        scope: fdk_asgi.types.Scope,
        receive: fdk_asgi.types.Receive,
        send: fdk_asgi.types.Send,
    ) -> None:
        # leave all but HTTP connection scopes untouched
        # note that websockets are not supported by fn
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        mapped_headers = [
            (FN_HTTP_REQUEST_URL, self._construct_request_url(scope)),
            (FN_HTTP_REQUEST_METHOD, scope["method"].encode()),
        ]
        for raw_key, value in scope["headers"]:
            if raw_key.lower() == b"content-type":
                mapped_headers.append((raw_key, value))
                continue
            mapped_headers.append((FN_HTTP_H_ + raw_key, value))
        scope["headers"] = mapped_headers

        scope["method"] = "POST"
        scope["path"] = "/call"

        await self.app(scope, receive, self._wrap_send(send))

    @staticmethod
    def _wrap_send(send: fdk_asgi.types.Send) -> fdk_asgi.types.Send:
        async def wrapped_send(message: fdk_asgi.types.Message) -> None:
            # only process messages of type=http.response.start,
            # leave message of other types untouched
            if message["type"] != "http.response.start":
                await send(message)
                return

            headers = Headers(list(message["headers"]))
            assert "content-type" in headers
            assert "fn-http-h-content-type" not in headers

            assert message["status"] in FN_ALLOWED_RESPONSE_CODES
            assert FN_HTTP_STATUS.decode() in headers
            status_code_header = headers.pop(FN_HTTP_STATUS.decode())
            try:
                message["status"] = int(status_code_header)
            except ValueError as exception:
                msg = f"{FN_HTTP_STATUS.decode()} header cannot be parsed as an integer"
                raise AssertionError(msg) from exception

            for key_lowercase in headers:
                if key_lowercase == "content-type":
                    continue

                assert key_lowercase.startswith("fn-")

            message["headers"] = Headers(
                [
                    (
                        key_raw[len(FN_HTTP_H_) :]
                        if key_raw.lower().startswith(FN_HTTP_H_)
                        else key_raw,
                        value_raw,
                    )
                    for key_raw, value_raw in headers.raw
                ]
            ).raw

            await send(message)

        return wrapped_send


class SaveOriginalScopeMiddleware:
    def __init__(self, app: fdk_asgi.types.ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: fdk_asgi.types.Scope,
        receive: fdk_asgi.types.Receive,
        send: fdk_asgi.types.Send,
    ) -> None:
        if scope["type"] == "http":
            assert scope["method"] == HTTPMethod.POST
            assert scope["path"] == "/call"
            scope.setdefault("extensions", {})["fdk-asgi.original-scope"] = {
                key: value for key, value in scope.items() if key != "extensions"
            }  # todo: replace with deep copy

        await self.app(scope, receive, send)


class ValidateMappedScope:
    def __init__(self, app: fdk_asgi.types.ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: fdk_asgi.types.Scope,
        receive: fdk_asgi.types.Receive,
        send: fdk_asgi.types.Send,
    ) -> None:
        if scope["type"] == "http":
            assert isinstance(scope["raw_path"], bytes)
            assert isinstance(scope["query_string"], bytes)
            for item in scope["headers"]:
                assert isinstance(item, tuple)
                key, value = item
                assert isinstance(key, bytes)
                assert isinstance(value, bytes)

        await self.app(scope, receive, send)
