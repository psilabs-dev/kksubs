from common.utils.coalesce import coalesce


def test_coalesce():
    assert coalesce(None, None, None) is None
    assert coalesce(1, 2, 3) == 1
    assert coalesce(1, None, None) == 1
    assert coalesce(None, 1, None) == 1
    assert coalesce() is None
