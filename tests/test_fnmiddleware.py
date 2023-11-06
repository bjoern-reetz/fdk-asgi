from fdk_asgi.app import FnMiddleware


def test_map_example_scope(mapped_scope):
    assert mapped_scope.mapped_scope == FnMiddleware.map_scope(mapped_scope.scope)
