from __future__ import annotations

from http import HTTPStatus


class FnMiddlewareError(Exception):
    code: HTTPStatus


class PathNotFoundError(FnMiddlewareError):
    code: HTTPStatus = HTTPStatus.NOT_FOUND

    def __init__(self, msg: str = "Path not found!"):
        super().__init__(msg)


class MethodNotAllowedError(FnMiddlewareError):
    code: HTTPStatus = HTTPStatus.METHOD_NOT_ALLOWED

    def __init__(self, msg: str = "Method not allowed!"):
        super().__init__(msg)


class MissingUrlError(FnMiddlewareError):
    code: HTTPStatus = HTTPStatus.BAD_REQUEST

    def __init__(self, msg: str = "Could not determine request URL!"):
        super().__init__(msg)


class MissingMethodError(FnMiddlewareError):
    code: HTTPStatus = HTTPStatus.BAD_REQUEST

    def __init__(self, msg: str = "Could not determine request method!"):
        super().__init__(msg)
