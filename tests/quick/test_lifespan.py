import typing
from contextlib import asynccontextmanager

from fdk_asgi.app import FnMiddleware
from starlette.applications import Starlette
from starlette.testclient import TestClient


def test_supports_lifespan_protocol() -> None:
    @asynccontextmanager
    async def lifespan(app: Starlette) -> typing.AsyncIterator[None]:
        app.state.startup_was_called = True
        yield
        app.state.shutdown_was_called = True

    app = Starlette(lifespan=lifespan)
    app.state.startup_was_called = False
    app.state.shutdown_was_called = False

    with TestClient(FnMiddleware(app)) as _:
        assert app.state.startup_was_called is True
        assert app.state.shutdown_was_called is False

    assert app.state.shutdown_was_called is True
