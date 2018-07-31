# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from sqlalchemy.exc import IntegrityError

from h.models import AuthClient
from h.models.auth_client import GrantType


class TestAuthClient(object):

    def test_has_id(self, client):
        assert client.id

    def test_does_not_allow_empty_redirect_uri_for_authz_code_grant(self, factories, db_session):
        client = factories.AuthClient.build(grant_type=GrantType.authorization_code, redirect_uri=None)
        db_session.add(client)

        with pytest.raises(IntegrityError):
            db_session.flush()

    @pytest.mark.parametrize('grant_type', [GrantType.client_credentials, GrantType.jwt_bearer, GrantType.password])
    def test_allows_empty_redirect_uri_for_other_grant(self, factories, db_session, grant_type):
        client = factories.AuthClient.build(grant_type=grant_type, redirect_uri=None)
        db_session.add(client)
        db_session.flush()

    def test_clientid_filter_by_returns_auth_client(self, factories, db_session):
        client = AuthClient(grant_type=GrantType.client_credentials, authority="foobar.baz")
        db_session.add(client)
        db_session.flush()

        clientid = "client:{id}@{authority}".format(id=client.id, authority=client.authority)

        result = db_session.query(AuthClient).filter_by(clientid=clientid).one()

        assert result.authority == "foobar.baz"
        assert result.id == client.id
        assert result.clientid == clientid

    def test_clientid_equals_query_with_invalid_clientid(self, db_session):
        # This is to ensure that we don't expose the ValueError that could
        # potentially be thrown by split_clientid.

        result = (db_session.query(AuthClient)
                  .filter_by(clientid='foobles.org')
                  .all())

        assert result == []

    def test_clientid_in_query(self, factories, db_session):
        fred = AuthClient(authority='example.net')
        alice = AuthClient(authority='foobar.com')

        db_session.add_all([fred, alice])  # not bob
        db_session.flush()

        result = (db_session.query(AuthClient)
                  .filter(AuthClient.clientid.in_([fred.clientid,
                                                   alice.clientid,
                                                   'client:04465aaa-8f73-11e8-91ca-8ba11742b240@nonexistent.foo']))
                  .all())

        assert len(result) == 2
        assert fred in result
        assert alice in result

    def test_it_does_not_raise_when_invalid_clientid_format_in_in_query(self, db_session):
        # This is to ensure that we don't expose the ValueError that could
        # potentially be thrown by split_client.

        fred = AuthClient(authority='example.net')
        db_session.add(fred)
        db_session.flush()

        result = (db_session.query(AuthClient)
                  .filter(AuthClient.clientid.in_([fred.clientid,
                                                  'invalid']))
                  .all())

        assert len(result) == 1
        assert fred in result

    def test_it_does_not_raise_when_invalid_uuid_in_in_query(self, db_session):
        # This is to ensure that we don't expose the ValueError that could
        # potentially be thrown by split_client.

        fred = AuthClient(authority='example.net')
        db_session.add(fred)
        db_session.flush()

        result = (db_session.query(AuthClient)
                  .filter(AuthClient.clientid.in_([fred.clientid,
                                                  'client:foo@bar.com']))
                  .all())

        assert len(result) == 1
        assert fred in result

    def test_it_doest_not_raise_when_in_query_only_contains_invalid_clientid(self, db_session):
        # This is to ensure that we don't expose the ValueError that could
        # potentially be thrown by split_user.

        result = (db_session.query(AuthClient)
                  .filter(AuthClient.clientid.in_(['client:foobles@baz']))
                  .all())

        assert result == []

    @pytest.fixture
    def client(self, db_session):
        client = AuthClient(authority='example.com')
        db_session.add(client)
        db_session.flush()
        return client
