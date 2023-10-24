import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, JSONResponse
from starlette.routing import Route, Mount
from starlette import status

from fdk_asgi import FnApplication


def homepage(_):
    return PlainTextResponse("Hello, world!")


def users_list(request: Request):
    return JSONResponse(request.app.state.users)


def users_get(request: Request):
    username = request.path_params["username"]
    try:
        user_obj = next(
            obj for obj in request.app.state.users if obj["username"] == username
        )
    except StopIteration:
        return PlainTextResponse(
            "User not in database!", status_code=status.HTTP_404_NOT_FOUND
        )
    return JSONResponse(user_obj)


async def users_create(request: Request):
    payload = await request.json()
    request.app.state.users.append(payload)
    return JSONResponse(payload, status_code=status.HTTP_201_CREATED)


routes = [
    Route("/", homepage),
    Route("/users", users_list),
    Route("/users/{username}", users_get),
    Route("/users/{username}", users_create, methods=["POST"]),
]


@pytest.fixture
def app():
    app = Starlette(debug=True, routes=routes)
    app.state.users = []
    return app


@pytest.fixture
def mounted_app(app):
    return Starlette(debug=True, routes=[Mount("/mounted", app=app)])


@pytest.fixture
def fn_app(app):
    return FnApplication(app)
