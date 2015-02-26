import pytest

from .. import security


def test_derive_key_consistent():
    k1 = security.derive_key('secret', 'h.foo')
    k2 = security.derive_key('secret', 'h.foo')
    assert k1 == k2


def test_derive_key_length():
    k1 = security.derive_key('secret', 'h.foo')
    assert len(k1) >= 64


def test_derive_key_missing_secret():
    with pytest.raises(ValueError):
        security.derive_key(None, 'h.foo')


def test_derive_key_missing_salt():
    with pytest.raises(ValueError):
        security.derive_key('secret', None)
