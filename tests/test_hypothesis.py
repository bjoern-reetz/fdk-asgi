import typing
from http import HTTPStatus

from fdk_asgi.app import FnMiddleware
from hypothesis import given
from hypothesis import strategies as st
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient
from starlette.types import ASGIApp

from .utils import HTTPMethod, InverseFnMiddleware, st_json


def homepage(_: Request):
    return PlainTextResponse("Homepage")


def respond_with_json(request: Request):
    return JSONResponse(request.app.state.json)


def respond_with_text(request: Request):
    return PlainTextResponse(request.app.state.text)


routes = [
    Route("/", homepage),
    Route(
        "/any.json", respond_with_json, methods=[method.value for method in HTTPMethod]
    ),
    Route(
        "/any.txt", respond_with_text, methods=[method.value for method in HTTPMethod]
    ),
    *(
        Route(
            f"/{method.value.lower()}.json", respond_with_json, methods=[method.value]
        )
        for method in HTTPMethod
    ),
    *(
        Route(f"/{method.value.lower()}.txt", respond_with_text, methods=[method.value])
        for method in HTTPMethod
    ),
]


def test_homepage():
    app = Starlette(routes=routes)

    with TestClient(
        typing.cast(ASGIApp, InverseFnMiddleware(FnMiddleware(app)))
    ) as client:
        response = client.get("/")
        assert response.status_code == HTTPStatus.OK
        assert "content-type" in response.headers
        assert response.headers["content-type"].startswith("text/plain")
        assert response.text == "Homepage"

        response = client.head("/")
        assert response.status_code == HTTPStatus.OK
        assert "content-type" in response.headers
        assert response.headers["content-type"].startswith("text/plain")

        for method in HTTPMethod:
            if method in [HTTPMethod.GET, HTTPMethod.HEAD]:
                continue

            response = client.request(method.value, "/")
            assert (
                response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
            ), f'{method.value} "/" should return status {HTTPStatus.METHOD_NOT_ALLOWED} METHOD_NOT_ALLOWED'


@given(method=st.sampled_from(HTTPMethod), data=st.text())
def test_body_text(method: HTTPMethod, data: str):
    app = Starlette(routes=routes)
    app.state.text = data

    with TestClient(
        typing.cast(ASGIApp, InverseFnMiddleware(FnMiddleware(app)))
    ) as client:
        response = client.request(method.value, f"/{method.value.lower()}.txt")
        assert response.status_code == HTTPStatus.OK
        assert "content-type" in response.headers
        assert response.headers["content-type"].startswith("text/plain")

        if method == HTTPMethod.HEAD:
            return

        assert response.text == data


@given(method=st.sampled_from(HTTPMethod), data=st_json())
def test_body_json(method: HTTPMethod, data: any):
    app = Starlette(routes=routes)
    app.state.json = data

    with TestClient(
        typing.cast(ASGIApp, InverseFnMiddleware(FnMiddleware(app)))
    ) as client:
        response = client.request(method.value, f"/{method.value.lower()}.json")
        assert response.status_code == HTTPStatus.OK
        assert "content-type" in response.headers
        assert response.headers["content-type"] == "application/json"

        if method == HTTPMethod.HEAD:
            return

        assert response.json() == data
