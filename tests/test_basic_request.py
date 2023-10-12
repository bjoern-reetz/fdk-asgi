from starlette.testclient import TestClient
from starlette import status


def test_foo(fn_app):
    client = TestClient(fn_app)
    response = client.post(
        "/call",
        headers={
            "Fn-Http-Request-Url": "https://foo.bar/",
            "Fn-Http-Request-Method": "GET",
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
