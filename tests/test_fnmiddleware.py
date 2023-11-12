def test_map_example_scope(mapped_scope, fn_app):
    assert mapped_scope.mapped_scope == fn_app.map_scope(mapped_scope.scope)
