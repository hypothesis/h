import pyramid.authorization
import pyramid.security
import pytest

import h.auth
from h.models import AuthClient
from h.traversal.auth_client import AuthClientRoot


class TestAuthClientRoot:
    def test_getitem_returns_the_right_AuthClient(self, db_session, pyramid_request):
        # Add a couple of noise AuthClients to the DB. It should not return these.
        db_session.add(AuthClient(authority="elifesciences.org"))
        db_session.add(AuthClient(authority="localhost"))

        # The AuthClient that we do expect it to return.
        expected_auth_client = AuthClient(authority="hypothes.is")
        db_session.add(expected_auth_client)

        db_session.flush()

        auth_client = AuthClientRoot(pyramid_request)[expected_auth_client.id]

        assert auth_client == expected_auth_client

    def test_getitem_returns_KeyError_if_no_AuthClients_in_DB(self, pyramid_request):
        auth_client_root = AuthClientRoot(pyramid_request)

        with pytest.raises(KeyError):
            auth_client_root["1d5937d6-73be-11e8-9125-871084ad92cf"]

    def test_getitem_returns_KeyError_if_no_matching_AuthClient_in_DB(
        self, db_session, pyramid_request
    ):
        # Add a couple of noise AuthClients to the DB. It should not return these.
        db_session.add(
            AuthClient(
                authority="elifesciences.org", id="c396be08-73bd-11e8-a791-e76551a909f6"
            )
        )
        db_session.add(
            AuthClient(authority="localhost", id="cf482552-73bd-11e8-a791-c37e5c2510d8")
        )

        auth_client_root = AuthClientRoot(pyramid_request)

        with pytest.raises(KeyError):
            auth_client_root["1d5937d6-73be-11e8-9125-871084ad92cf"]

    def test_getitem_returns_KeyError_if_client_id_is_invalid(self, pyramid_request):
        auth_client_root = AuthClientRoot(pyramid_request)

        with pytest.raises(KeyError):
            auth_client_root["this_is_not_a_valid_UUID"]

    @pytest.mark.parametrize("permission", ("foo", "bar", "admin_oauthclients"))
    def test_getitem_grants_admins_all_permissions_on_the_AuthClient(
        self, db_session, permission, pyramid_request
    ):
        auth_client = AuthClient(authority="hypothes.is")
        db_session.add(auth_client)
        db_session.flush()
        auth_policy = pyramid.authorization.ACLAuthorizationPolicy()

        auth_client = AuthClientRoot(pyramid_request)[auth_client.id]

        assert auth_policy.permits(
            context=auth_client, principals=(h.auth.role.Admin,), permission=permission
        )

    @pytest.mark.parametrize("permission", ("foo", "bar", "admin_oauthclients"))
    def test_getitem_doesnt_grant_non_admins_all_permissions_on_the_AuthClient(
        self, db_session, factories, permission, pyramid_request
    ):
        user = factories.User()
        auth_client = AuthClient(authority="hypothes.is")
        db_session.add(auth_client)
        db_session.flush()
        auth_policy = pyramid.authorization.ACLAuthorizationPolicy()

        auth_client = AuthClientRoot(pyramid_request)[auth_client.id]

        assert not auth_policy.permits(
            context=auth_client,
            # Simulate the principals that a real non-admin request would have: lots of
            # principals but not h.auth.role.Admin.
            principals=(
                pyramid.security.Everyone,
                pyramid.security.Authenticated,
                h.auth.role.Staff,
                "group:__world__",
                "authority:example.com",
                user.userid,
            ),
            permission=permission,
        )
