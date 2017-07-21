# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from h.models import AuthClient


class TestAuthClient(object):

    def test_has_id(self, client):
        assert client.id

    @pytest.fixture
    def client(self, db_session):
        client = AuthClient(authority='example.com')
        db_session.add(client)
        db_session.flush()
        return client
