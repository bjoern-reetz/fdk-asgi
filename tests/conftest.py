from dataclasses import dataclass

import pytest
from asgiref.typing import HTTPScope
from starlette import status
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route

from fdk_asgi.app import FnMiddleware


def homepage(_: Request):
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


def app_factory(users=None):
    app = Starlette(debug=True, routes=routes)
    app.state.users = users or []
    return app


@pytest.fixture
def app():
    return app_factory()


@pytest.fixture
def mounted_app(app):
    return Starlette(debug=True, routes=[Mount("/mounted", app=app)])


@pytest.fixture
def fn_app(app):
    return FnMiddleware(app)


@dataclass
class MappedScope:
    """A pair of scope that's coming in from the Function agent,
    and it's mapped version that will be passed to the ASGI app."""

    scope: HTTPScope
    mapped_scope: HTTPScope


@pytest.fixture
def mapped_scope():
    # todo: use a mock instead of accessing the implementation (i.e. the static methods)
    return MappedScope(
        scope={
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "server": None,
            "client": None,
            "scheme": "http",
            "root_path": "",
            "headers": [
                (b"host", b"localhost"),
                (b"user-agent", b"lua-resty-http/0.16.1 (Lua) ngx_lua/10020"),
                (b"transfer-encoding", b"chunked"),
                (b"content-type", b"application/octet-stream"),
                (b"date", b"Mon, 06 Nov 2023 16:44:57 GMT"),
                (b"fn-call-id", b"01HEJRBSQ51BT0D2GZJ01EVJQE"),
                (b"fn-deadline", b"2023-11-06T16:45:29Z"),
                (b"fn-http-h-accept", b"*/*"),
                (b"fn-http-h-cdn-loop", b"ptAeOAHRrYjjOEF75MRX6w"),
                (b"fn-http-h-content-type", b"application/octet-stream"),
                (b"fn-http-h-forwarded", b"for=123.123.123.123"),
                (
                    b"fn-http-h-host",
                    b"icz...fe4.apigateway.eu-frankfurt-1.oci.customer-oci.com",
                ),
                (b"fn-http-h-user-agent", b"curl/7.81.0"),
                (b"fn-http-h-x-forwarded-for", b"123.123.123.123"),
                (b"fn-http-h-x-real-ip", b"123.123.123.123"),
                (b"fn-http-method", b"GET"),
                (b"fn-http-request-url", b"/"),
                (b"fn-intent", b"httprequest"),
                (b"fn-invoke-type", b"sync"),
                (
                    b"oci-subject-compartment-id",
                    b"ocid1.compartment.oc1..aaa...o2a",
                ),
                (
                    b"oci-subject-id",
                    b"ocid1.apigateway.oc1.eu-frankfurt-1.ama...owa",
                ),
                (
                    b"oci-subject-tenancy-id",
                    b"ocid1.tenancy.oc1..aaa...5ua",
                ),
                (b"oci-subject-type", b"resource"),
                (
                    b"opc-request-id",
                    b"/44F...Q4D",
                ),
                (b"x-content-sha256", b"47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU="),
                (b"accept-encoding", b"gzip"),
            ],
            "state": {},
            "method": "POST",
            "path": "/call",
            "raw_path": b"/call",
            "query_string": b"",
            "path_params": {},
        },
        mapped_scope={
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "server": None,
            "client": None,
            "scheme": "http",
            "root_path": "",
            "headers": [
                (b"host", b"localhost"),
                (b"user-agent", b"lua-resty-http/0.16.1 (Lua) ngx_lua/10020"),
                (b"transfer-encoding", b"chunked"),
                (b"content-type", b"application/octet-stream"),
                (b"date", b"Mon, 06 Nov 2023 16:44:57 GMT"),
                (b"fn-call-id", b"01HEJRBSQ51BT0D2GZJ01EVJQE"),
                (b"fn-deadline", b"2023-11-06T16:45:29Z"),
                (b"accept", b"*/*"),
                (b"cdn-loop", b"ptAeOAHRrYjjOEF75MRX6w"),
                (b"content-type", b"application/octet-stream"),
                (b"forwarded", b"for=123.123.123.123"),
                (
                    b"host",
                    b"icz...fe4.apigateway.eu-frankfurt-1.oci.customer-oci.com",
                ),
                (b"user-agent", b"curl/7.81.0"),
                (b"x-forwarded-for", b"123.123.123.123"),
                (b"x-real-ip", b"123.123.123.123"),
                (b"fn-intent", b"httprequest"),
                (b"fn-invoke-type", b"sync"),
                (
                    b"oci-subject-compartment-id",
                    b"ocid1.compartment.oc1..aaa...o2a",
                ),
                (
                    b"oci-subject-id",
                    b"ocid1.apigateway.oc1.eu-frankfurt-1.ama...owa",
                ),
                (
                    b"oci-subject-tenancy-id",
                    b"ocid1.tenancy.oc1..aaa...5ua",
                ),
                (b"oci-subject-type", b"resource"),
                (
                    b"opc-request-id",
                    b"/44F...Q4D",
                ),
                (b"x-content-sha256", b"47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU="),
                (b"accept-encoding", b"gzip"),
            ],
            "state": {},
            "method": "GET",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "path_params": {},
        },
    )
