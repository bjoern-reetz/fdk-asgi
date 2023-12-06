from fdk_asgi.app import FN_HTTP_REQUEST_METHOD, FN_HTTP_REQUEST_URL
from starlette import status
from starlette.testclient import TestClient


def test_foo(fn_app):
    client = TestClient(fn_app)
    response = client.post(
        "/call",
        headers={
            FN_HTTP_REQUEST_URL: "https://foo.bar/users",
            FN_HTTP_REQUEST_METHOD: "GET",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

    user_obj = {
        "username": "foo",
    }
    response = client.post(
        "/call",
        headers={
            FN_HTTP_REQUEST_URL: f"https://foo.bar/users/{user_obj['username']}",
            FN_HTTP_REQUEST_METHOD: "POST",
        },
        json=user_obj,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Fn-Http-Status"] == str(status.HTTP_201_CREATED)
    assert response.headers["content-type"] == "application/json"
    assert response.json() == user_obj


def test_illegal_call(fn_app):
    client = TestClient(fn_app)

    response = client.get("/call")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    response = client.post("/call/users")
    assert response.status_code == status.HTTP_404_NOT_FOUND
