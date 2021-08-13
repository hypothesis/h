from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h.security import Identity
from h.security.principals import principals_for_identity, principals_for_userid
from h.security.role import Role


class TestPrincipalsForUserid:
    def test_it(self, pyramid_request, user_service, principals_for_identity):
        result = principals_for_userid(sentinel.userid, pyramid_request)

        user_service.fetch.assert_called_once_with(sentinel.userid)
        principals_for_identity.assert_called_once_with(
            Any.instance_of(Identity).with_attrs(
                {"user": user_service.fetch.return_value}
            )
        )
        assert result == principals_for_identity.return_value

    @pytest.fixture
    def principals_for_identity(self, patch):
        return patch("h.security.principals.principals_for_identity")


class TestPrincipalsForIdentity:
    def test_it_with_None(self):
        assert principals_for_identity(None) is None

    def test_it_with_an_empty_identity(self):
        assert principals_for_identity(Identity()) is None

    @pytest.mark.parametrize("admin", (True, False))
    @pytest.mark.parametrize("staff", (True, False))
    @pytest.mark.parametrize("with_auth_client", (True, False))
    def test_user_principals(self, identity, admin, staff, with_auth_client):
        identity.user.admin = admin
        identity.user.staff = staff

        if not with_auth_client:
            identity.auth_client = None

        principals = principals_for_identity(identity)

        assert Role.USER in principals
        assert f"authority:{identity.user.authority}" in principals
        for group in identity.user.groups:
            assert f"group:{group.pubid}" in principals

        assert bool(Role.ADMIN in principals) == admin
        assert bool(Role.STAFF in principals) == staff

    @pytest.mark.parametrize("with_user", (True, False))
    def test_auth_client_principals(self, identity, with_user):
        if not with_user:
            identity.user = None

        principals = principals_for_identity(identity)

        auth_client = identity.auth_client
        assert f"client:{auth_client.id}@{auth_client.authority}" in principals
        assert f"client_authority:{auth_client.authority}" in principals
        assert Role.AUTH_CLIENT in principals

    def test_auth_client_and_user_principals(self, identity):
        principals = principals_for_identity(identity)

        assert identity.user.userid in principals
        assert Role.AUTH_CLIENT_FORWARDED_USER in principals

    @pytest.fixture
    def identity(self, factories):
        return Identity(
            user=factories.User(groups=factories.Group.create_batch(2)),
            auth_client=factories.AuthClient(),
        )
