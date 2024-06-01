import fdk_asgi.types
from starlette.testclient import TestClient


def test_mounted_app(mounted_app: fdk_asgi.types.ASGIApp) -> None:
    client = TestClient(mounted_app)
    response = client.get("/mounted/")
    assert response.content == b"Hello, world!"
