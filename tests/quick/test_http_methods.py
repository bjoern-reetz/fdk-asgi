from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient


def test_http_methods() -> None:
    supported_methods = [
        "GET",
        "HEAD",
        "POST",
        "PUT",
        "DELETE",
        # "CONNECT",  # not sure if Starlette supports it
        "OPTIONS",
        "TRACE",
        "PATCH",
    ]

    def remember_method(request: Request) -> PlainTextResponse:
        request.app.state.handled_methods.add(request.method)
        return PlainTextResponse(
            f"I will remember the request method {request.method}."
        )

    app = Starlette(routes=[Route("/", remember_method, methods=supported_methods)])
    app.state.handled_methods = set()

    client = TestClient(app)
    for method in supported_methods:
        client.request(method, "/", json={"also_include": "some-data"})
    assert app.state.handled_methods == set(supported_methods)
