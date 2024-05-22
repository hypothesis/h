from unittest.mock import Mock

from h.models import helpers


def test_repr_():
    obj = Mock(foo="FOO", bar="BAR")

    assert helpers.repr_(obj, ["foo", "bar"]) == "Mock(foo='FOO', bar='BAR')"
