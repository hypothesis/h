# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from passlib.context import CryptContext

from h.security import password_context


def test_password_context():
    assert isinstance(password_context, CryptContext)
    assert len(password_context.schemes()) > 0
