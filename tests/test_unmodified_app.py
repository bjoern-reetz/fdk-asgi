from starlette import status
from starlette.testclient import TestClient


def test_homepage(app):
    client = TestClient(app)
    response = client.get("/")
    assert response.content == b"Hello, world!"


def test_users(app):
    client = TestClient(app)

    response = client.get("/users")
    assert response.json() == []

    username = "foo-bar"
    email = "foo@bar.baz"
    user_url = "/users/%s" % username

    response = client.get(user_url)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    payload = {"username": username, "email": email}
    response = client.post(user_url, json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == payload

    response = client.get(user_url)
    assert response.status_code == status.HTTP_200_OK
    user_obj = response.json()
    assert user_obj == payload
