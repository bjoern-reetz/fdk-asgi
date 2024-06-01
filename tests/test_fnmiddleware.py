from fdk_asgi.app import FnMiddleware

from .conftest import MappedScope


def test_map_example_scope(mapped_scope: MappedScope, fn_app: FnMiddleware) -> None:
    assert mapped_scope.mapped_scope == fn_app._map_http_scope(mapped_scope.scope)
