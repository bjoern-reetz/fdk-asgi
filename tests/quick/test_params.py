from typing import Optional

import pytest
from httpx import Headers
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient

last_request: Optional[Request] = None


async def handler(request: Request) -> Response:
    global last_request
    last_request = request
    return PlainTextResponse("Hello world")


routes = [
    Route("/", handler),
    Route("/{my_param}", handler, methods=["GET", "POST"]),
]

app = Starlette(routes=routes)
client = TestClient(app)


def test_path_params() -> None:
    client.get("/without-trailing-slash")
    assert last_request is not None
    assert last_request.path_params == {"my_param": "without-trailing-slash"}

    client.get("/with-trailing-slash/")
    assert last_request is not None
    assert last_request.path_params == {"my_param": "with-trailing-slash"}


def test_query_params() -> None:
    params = {"foo": "bar", "one": "two"}
    client.get("/with-simple-query-params", params=params)
    assert last_request is not None
    assert last_request.query_params["foo"] == params["foo"]

    multi_params = {"multi-foo": ["bar", "bar-again"], "foo": ["bar"]}
    client.get("/with-multi-query-params", params=multi_params)
    assert set(last_request.query_params.multi_items()) == {
        (key, value)
        for key, multi_value in multi_params.items()
        for value in multi_value
    }


@pytest.mark.anyio()
async def test_body() -> None:
    payload = {"a simple": "json payload"}
    client.post("/with-body", json=payload)
    assert last_request is not None
    assert await last_request.json() == payload


def test_header() -> None:
    headers = Headers(
        [
            ("key1", "value"),
            ("key2", "value"),
        ]
    )
    client.get("/with-headers", headers=headers)
    assert last_request is not None
    assert set(last_request.headers.items()).issuperset(headers.multi_items())


@pytest.mark.anyio()
async def test_form_data() -> None:
    data = {"foo": "bar", "one": "two"}
    client.post("/with-simple-form-data", data=data)
    assert last_request is not None
    assert (await last_request.form()).items() == set(data.items())

    multi_params = {"multi-foo": ["bar", "bar-again"], "foo": ["bar"]}
    client.post("/with-multi-form-data", params=multi_params)
    assert last_request is not None
    assert set(last_request.query_params.multi_items()) == {
        (key, value)
        for key, multi_value in multi_params.items()
        for value in multi_value
    }
