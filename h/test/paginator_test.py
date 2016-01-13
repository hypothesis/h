# -*- coding: utf-8 -*-

from pyramid.testing import DummyRequest
import pytest

from h.paginator import paginate


class FakeQuery(object):

    """
    A helper class to fake out the fluent API of a SQLAlchemy Query object.
    """

    def __init__(self, total):
        self.total = total
        self.offset_param = None
        self.limit_param = None
        self.all_called = False

    def count(self):
        return self.total

    def offset(self, n):
        self.offset_param = n
        return self

    def limit(self, n):
        self.limit_param = n
        return self

    def all(self):
        self.all_called = True
        return self


def fake_view(total):
    """
    Make a fake view function and a mock query object for testing.
    """
    query = FakeQuery(total)

    def view(context, request):
        return query

    return query, view


def test_paginate_returns_resultset():
    request = DummyRequest()
    query, view = fake_view(total=10)

    wrapped = paginate(view)
    result = wrapped(context=None, request=request)

    assert result['results'] == query
    # Assert that .all() has been called to turn the query into a list.
    assert query.all_called


@pytest.mark.parametrize('total', [10, 20, 40, 87])
def test_paginate_includes_total(total):
    request = DummyRequest()
    query, view = fake_view(total=total)

    wrapped = paginate(view)
    result = wrapped(context=None, request=request)

    assert result['total'] == total


@pytest.mark.parametrize('total,param,offset', [
    # When there are no items:
    (0, '1', 0),
    (0, '2', 0),

    # When there are N * PAGE_SIZE items:
    (20, '1', 0),
    (20, '2', 0),
    (40, '1', 0),
    (40, '2', 20),
    (40, '3', 20),

    # When the number of items doesn't fit perfectly into N pages:
    (25, '1', 0),
    (25, '2', 20),
    (25, '3', 20),

    # Some extreme cases:
    (400, '20', 380),

    # Junk data should be discarded:
    (100, '0', 0),
    (100, '999e9', 0),
    (100, 'fish', 0),
    (400, '-19000', 0),
    (400, '?????', 0),
])
def test_paginate_returns_offsets_and_limits_resultset(total, param, offset):
    request = DummyRequest(params={'page': param})
    query, view = fake_view(total)

    wrapped = paginate(view)
    result = wrapped(context=None, request=request)

    assert result['results'].offset_param == offset
    assert result['results'].limit_param == 20


@pytest.mark.parametrize('total,param,meta', [
    # When there are no items:
    (0, '1', (1, 1, None, None)),
    (0, '2', (1, 1, None, None)),

    # When there are N * PAGE_SIZE items:
    (20, '1', (1, 1, None, None)),
    (20, '2', (1, 1, None, None)),
    (40, '1', (1, 2, 2, None)),
    (40, '2', (2, 2, None, 1)),
    (40, '3', (2, 2, None, 1)),

    # When the number of items doesn't fit perfectly into N pages:
    (25, '1', (1, 2, 2, None)),
    (25, '2', (2, 2, None, 1)),
    (25, '3', (2, 2, None, 1)),

    # Some extreme cases:
    (400, '19', (19, 20, 20, 18)),

    # Junk data should be discarded:
    (100, '999e9', (1, 5, 2, None)),
    (100, 'fish',  (1, 5, 2, None)),
    (400, '-19000', (1, 20, 2, None)),
    (400, '?????', (1, 20, 2, None)),
])
def test_paginate_returns_page_metadata(total, param, meta):
    request = DummyRequest(params={'page': param})
    query, view = fake_view(total)
    ecur, emax, enext, eprev = meta

    wrapped = paginate(view)
    result = wrapped(context=None, request=request)

    assert result['page'] == {
        'cur': ecur,
        'max': emax,
        'next': enext,
        'prev': eprev,
    }


def test_paginate_params():
    request = DummyRequest(params={'page': 2})
    query, view = fake_view(20)

    decorator = paginate(page_size=5)
    wrapped = decorator(view)
    result = wrapped(context=None, request=request)

    assert result['results'].offset_param == 5
    assert result['results'].limit_param == 5
