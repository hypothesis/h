# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import pytest

from h.util import auth_client as client_util


def test_split_client():
    parts = client_util.split_client("client:04465aaa-8f73-11e8-91ca-8ba11742b240@hypothes.is")
    assert parts == {'id': '04465aaa-8f73-11e8-91ca-8ba11742b240', 'authority': 'hypothes.is'}


def test_split_client_no_match():
    with pytest.raises(ValueError):
        client_util.split_client("donkeys")
