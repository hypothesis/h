# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import string

from passlib.context import CryptContext
from hypothesis import assume
from hypothesis import strategies as st
from hypothesis import given

from h._compat import text_type
from h.security import derive_key
from h.security import password_context
from h.security import token_urlsafe

REASONABLE_INFO = st.text(alphabet=string.printable)
REASONABLE_KEY_MATERIAL = st.binary(min_size=8, max_size=128)
REASONABLE_SALT = st.binary(min_size=64, max_size=64)


class TestDeriveKey(object):
    @given(info_a=REASONABLE_INFO,
           info_b=REASONABLE_INFO,
           key=REASONABLE_KEY_MATERIAL,
           salt=REASONABLE_SALT)
    def test_different_info_different_output(self, info_a, info_b, key, salt):
        """
        For fixed key material and salt, derive_key should give different output
        for differing info parameters.
        """
        assume(info_a != info_b)

        info_a_bytes = info_a.encode('utf-8')
        info_b_bytes = info_b.encode('utf-8')

        derived_a = derive_key(key, salt, info_a_bytes)
        derived_b = derive_key(key, salt, info_b_bytes)

        assert derived_a != derived_b

    @given(info=REASONABLE_INFO,
           key_a=REASONABLE_KEY_MATERIAL,
           key_b=REASONABLE_KEY_MATERIAL,
           salt=REASONABLE_SALT)
    def test_different_key_different_output(self, info, key_a, key_b, salt):
        """If the key is rotated, the output should change."""
        assume(key_a != key_b)

        info_bytes = info.encode('utf-8')

        derived_a = derive_key(key_a, salt, info_bytes)
        derived_b = derive_key(key_b, salt, info_bytes)

        assert derived_a != derived_b

    @given(info=REASONABLE_INFO,
           key=REASONABLE_KEY_MATERIAL,
           salt_a=REASONABLE_SALT,
           salt_b=REASONABLE_SALT)
    def test_different_salt_different_output(self, info, key, salt_a, salt_b):
        """If the salt is changed, the output should change."""
        assume(salt_a != salt_b)

        info_bytes = info.encode('utf-8')

        derived_a = derive_key(key, salt_a, info_bytes)
        derived_b = derive_key(key, salt_b, info_bytes)

        assert derived_a != derived_b

    @given(info=REASONABLE_INFO,
           key=REASONABLE_KEY_MATERIAL,
           salt=REASONABLE_SALT)
    def test_consistent_output(self, info, key, salt):
        """For fixed key, salt, info, the output should be constant."""
        info_bytes = info.encode('utf-8')

        derived_a = derive_key(key, salt, info_bytes)
        derived_b = derive_key(key, salt, info_bytes)

        assert derived_a == derived_b

    @given(info=REASONABLE_INFO,
           key=REASONABLE_KEY_MATERIAL,
           salt=REASONABLE_SALT)
    def test_output(self, info, key, salt):
        info_bytes = info.encode('utf-8')

        derived = derive_key(key, salt, info_bytes)

        assert len(derived) == 64

    def test_it_encodes_str_key_material(self):
        derived = derive_key('akey', b'somesalt', b'some-info')
        assert len(derived) == 64


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
