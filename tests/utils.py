from string import printable

from hypothesis import strategies as st


def st_json(*, max_leaves=5):
    return st.recursive(
        st.none()
        | st.booleans()
        | st.floats(allow_nan=False, allow_infinity=False, allow_subnormal=False)
        | st.text(printable),
        lambda children: st.lists(children)
        | st.dictionaries(st.text(printable), children),
        max_leaves=max_leaves,
    )
