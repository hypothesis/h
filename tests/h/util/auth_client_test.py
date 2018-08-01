# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import pytest

from h.util import auth_client as client_util


class TestSplitClient(object):

    def test_it_splits_valid_client_id(self):
        parts = client_util.split_client("client:04465aaa-8f73-11e8-91ca-8ba11742b240@hypothes.is")
        assert parts == {'id': '04465aaa-8f73-11e8-91ca-8ba11742b240', 'authority': 'hypothes.is'}

    def test_it_raises_if_clientid_format_invalid(self):
        with pytest.raises(ValueError):
            client_util.split_client("donkeys")

    def test_it_raises_if_client_id_is_invalid_uuid(self):
        with pytest.raises(ValueError):
            client_util.split_client("client:foobar@whatever.baz")
