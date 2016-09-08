# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from passlib.context import CryptContext
from hypothesis import strategies as st
from hypothesis import given

from h._compat import text_type
from h.security import password_context
from h.security import token_urlsafe


def test_password_context():
    assert isinstance(password_context, CryptContext)
    assert len(password_context.schemes()) > 0


@given(nbytes=st.integers(min_value=1, max_value=64))
def test_token_urlsafe(nbytes):
    tok = token_urlsafe(nbytes)

    # Should be text
    assert isinstance(tok, text_type)
    # Always at least nbytes of data
    assert len(tok) > nbytes


def test_token_urlsafe_no_args():
    tok = token_urlsafe()

    assert isinstance(tok, text_type)
    assert len(tok) > 32
