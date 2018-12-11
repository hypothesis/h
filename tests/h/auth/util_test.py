# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import namedtuple

import pytest
import mock
import sqlalchemy as sa

from pyramid import security

from h.auth import role
from h.auth import util
from h._compat import text_type
from h.models.auth_client import GrantType
from h.models import AuthClient
from h.services.user import UserService

FakeUser = namedtuple("FakeUser", ["authority", "admin", "staff", "groups"])
FakeGroup = namedtuple("FakeGroup", ["pubid"])


class TestGroupfinder(object):
    def test_it_fetches_the_user(self, pyramid_request, user_service):
        util.groupfinder("acct:bob@example.org", pyramid_request)
        user_service.fetch.assert_called_once_with("acct:bob@example.org")

    def test_it_returns_principals_for_user(
        self, pyramid_request, user_service, principals_for_user
    ):
        result = util.groupfinder("acct:bob@example.org", pyramid_request)

        principals_for_user.assert_called_once_with(user_service.fetch.return_value)
        assert result == principals_for_user.return_value


@pytest.mark.parametrize(
    "user,principals",
    (
        # User isn't found in the database: they're not authenticated at all
        (None, None),
        # User found but not staff, admin, or a member of any groups: only role is role.User
        (
            FakeUser(authority="example.com", admin=False, staff=False, groups=[]),
            ["authority:example.com", role.User],
        ),
        # User is admin: role.Admin should be in principals
        (
            FakeUser(authority="foobar.org", admin=True, staff=False, groups=[]),
            ["authority:foobar.org", role.Admin, role.User],
        ),
        # User is staff: role.Staff should be in principals
        (
            FakeUser(authority="example.com", admin=False, staff=True, groups=[]),
            ["authority:example.com", role.Staff, role.User],
        ),
        # User is admin and staff
        (
            FakeUser(authority="foobar.org", admin=True, staff=True, groups=[]),
            ["authority:foobar.org", role.Admin, role.Staff, role.User],
        ),
        # User is a member of some groups
        (
            FakeUser(
                authority="example.com",
                admin=False,
                staff=False,
                groups=[FakeGroup("giraffe"), FakeGroup("elephant")],
            ),
            ["authority:example.com", "group:giraffe", "group:elephant", role.User],
        ),
        # User is admin, staff, and a member of some groups
        (
            FakeUser(
                authority="foobar.org",
                admin=True,
                staff=True,
                groups=[FakeGroup("donkeys")],
            ),
            [
                "authority:foobar.org",
                "group:donkeys",
                role.Admin,
                role.Staff,
                role.User,
            ],
        ),
    ),
)
def test_principals_for_user(user, principals):
    result = util.principals_for_user(user)

    if principals is None:
        assert result is None
    else:
        assert set(principals) == set(result)


@pytest.mark.parametrize(
    "p_in,p_out",
    [
        # The basics
        ([], []),
        (["acct:donna@example.com"], ["acct:donna@example.com"]),
        (["group:foo"], ["group:foo"]),
        # Remove pyramid principals
        (["system.Everyone"], []),
        # Remap annotatator principal names
        (["group:__world__"], [security.Everyone]),
        # Normalise multiple principals
        (
            ["me", "myself", "me", "group:__world__", "group:foo", "system.Admins"],
            ["me", "myself", security.Everyone, "group:foo"],
        ),
    ],
)
def test_translate_annotation_principals(p_in, p_out):
    result = util.translate_annotation_principals(p_in)

    assert set(result) == set(p_out)


class TestClientAuthority(object):
    @pytest.mark.parametrize(
        "principals",
        [
            ["foo", "bar", "baz"],
            ["authority", "foo"],
            [],
            ["client_authority:"],
            [" client_authority:biz.biz", "foo"],
            ["client_authority :biz.biz", "foo"],
        ],
    )
    def test_it_returns_None_if_no_client_authority_principal_match(
        self, principals, pyramid_request, pyramid_config
    ):
        pyramid_config.testing_securitypolicy("LYZADOODLE", groupids=principals)

        assert util.client_authority(pyramid_request) is None

    @pytest.mark.parametrize(
        "principals,authority",
        [
            (
                ["foo", "bar", "baz", "client_authority:felicitous.com"],
                "felicitous.com",
            ),
            (["client_authority:somebody.likes.me", "foo"], "somebody.likes.me"),
        ],
    )
    def test_it_returns_authority_if_authority_principal_matchpyramid_requesi(
        self, principals, authority, pyramid_request, pyramid_config
    ):
        pyramid_config.testing_securitypolicy("LYZADOODLE", groupids=principals)

        assert util.client_authority(pyramid_request) == authority


class TestAuthDomain(object):
    def test_it_returns_the_request_domain_if_authority_isnt_set(self, pyramid_request):
        # Make sure h.authority isn't set.
        pyramid_request.registry.settings.pop("h.authority", None)

        assert util.default_authority(pyramid_request) == pyramid_request.domain

    def test_it_allows_overriding_request_domain(self, pyramid_request):
        pyramid_request.registry.settings["h.authority"] = "foo.org"
        assert util.default_authority(pyramid_request) == "foo.org"

    def test_it_returns_text_type(self, pyramid_request):
        pyramid_request.domain = str(pyramid_request.domain)
        assert type(util.default_authority(pyramid_request)) == text_type


class TestPrincipalsForAuthClient(object):
    def test_it_sets_auth_client_principal(self, auth_client):
        principals = util.principals_for_auth_client(auth_client)

        assert (
            "client:{client_id}@{authority}".format(
                client_id=auth_client.id, authority=auth_client.authority
            )
            in principals
        )

    def test_it_sets_client_authority_principal(self, auth_client):
        principals = util.principals_for_auth_client(auth_client)

        assert (
            "client_authority:{authority}".format(authority=auth_client.authority)
            in principals
        )

    def test_it_sets_authclient_role(self, auth_client):
        principals = util.principals_for_auth_client(auth_client)

        assert role.AuthClient in principals

    def test_it_does_not_set_user_role(self, auth_client):
        principals = util.principals_for_auth_client(auth_client)

        assert role.User not in principals

    def test_it_returns_principals_as_list(self, auth_client):
        principals = util.principals_for_auth_client(auth_client)

        assert isinstance(principals, list)


class TestPrincipalsForAuthClientUser(object):
    def test_it_proxies_to_principals_for_user(
        self, principals_for_user, factories, auth_client
    ):
        user = factories.User()
        util.principals_for_auth_client_user(user, auth_client)

        principals_for_user.assert_called_once_with(user)

    def test_it_proxies_to_principals_for_auth_client(
        self, principals_for_auth_client, factories, auth_client
    ):
        util.principals_for_auth_client_user(factories.User(), auth_client)

        principals_for_auth_client.assert_called_once_with(auth_client)

    def test_it_adds_the_userid_principal(self, factories, auth_client):
        user = factories.User(authority=auth_client.authority)

        principals = util.principals_for_auth_client_user(user, auth_client)

        assert user.userid in principals

    def test_it_adds_the_authclientuser_role(self, factories, auth_client):
        user = factories.User(authority=auth_client.authority)

        principals = util.principals_for_auth_client_user(user, auth_client)

        assert role.AuthClientUser in principals

    def test_it_returns_combined_principals(self, factories, auth_client):
        user = factories.User(authority=auth_client.authority)
        group = factories.Group()
        user.groups.append(group)

        principals = util.principals_for_auth_client_user(user, auth_client)

        assert "group:{pubid}".format(pubid=group.pubid) in principals
        assert (
            "client:{client_id}@{authority}".format(
                client_id=auth_client.id, authority=auth_client.authority
            )
            in principals
        )
        assert "authority:{authority}".format(authority=auth_client.authority)
        assert role.AuthClient in principals


class TestVerifyAuthClient(object):
    def test_it_queries_for_auth_client_in_db(self, pyramid_request):
        pyramid_request.db.query.return_value.get.return_value = None
        util.verify_auth_client(
            client_id="whatever", client_secret="random", db_session=pyramid_request.db
        )

        pyramid_request.db.query.assert_called_once_with(AuthClient)
        pyramid_request.db.query.return_value.get.assert_called_once_with("whatever")

    def test_it_handles_sa_statement_exception_if_client_id_malformed(
        self, pyramid_request
    ):
        pyramid_request.db.query.return_value.get.side_effect = sa.exc.StatementError(
            message="You did it wrong", statement=None, params=None, orig=None
        )

        # does not raise
        util.verify_auth_client(
            client_id="malformed", client_secret="random", db_session=pyramid_request.db
        )

    def test_it_returns_None_if_client_id_malformed(self, pyramid_request):
        pyramid_request.db.query.return_value.get.side_effect = sa.exc.StatementError(
            message="You did it wrong", statement=None, params=None, orig=None
        )

        # does not raise
        principals = util.verify_auth_client(
            client_id="malformed", client_secret="random", db_session=pyramid_request.db
        )

        assert principals is None

    def test_it_returns_None_if_no_authclient_record_found_in_db(self, pyramid_request):
        pyramid_request.db.query.return_value.get.return_value = None
        principals = util.verify_auth_client(
            client_id="whatever", client_secret="random", db_session=pyramid_request.db
        )

        assert principals is None

    def test_it_returns_None_if_client_secret_is_None(self, pyramid_request, factories):
        insecure_auth_client = factories.AuthClient()
        pyramid_request.db.query.return_value.get.return_value = insecure_auth_client

        principals = util.verify_auth_client(
            client_id="whatever", client_secret="random", db_session=pyramid_request.db
        )

        assert insecure_auth_client.secret is None
        assert principals is None

    def test_it_returns_None_if_grant_type_is_not_client_credentials(
        self, pyramid_request, factories
    ):
        auth_code_client = factories.ConfidentialAuthClient(
            authority="weylandindustries.com", grant_type=GrantType.authorization_code
        )
        pyramid_request.db.query.return_value.get.return_value = auth_code_client

        principals = util.verify_auth_client(
            client_id="whatever", client_secret="random", db_session=pyramid_request.db
        )

        assert auth_code_client.grant_type == GrantType.authorization_code
        assert principals is None

    def test_it_uses_key_hashing_on_client_secret_for_message_authentication(
        self, pyramid_request, hmac, auth_client
    ):
        pyramid_request.db.query.return_value.get.return_value = auth_client

        util.verify_auth_client(
            client_id="whatever", client_secret="random", db_session=pyramid_request.db
        )

        hmac.compare_digest.assert_called_once_with(auth_client.secret, "random")

    def test_it_returns_None_if_hmac_hashing_match_fails_on_client_secret(
        self, pyramid_request, hmac, auth_client
    ):
        pyramid_request.db.query.return_value.get.return_value = auth_client
        hmac.compare_digest.return_value = False

        principals = util.verify_auth_client(
            client_id="whatever", client_secret="random", db_session=pyramid_request.db
        )

        assert principals is None

    @pytest.fixture
    def pyramid_request(self, pyramid_request, db_session):
        pyramid_request.db = mock.create_autospec(
            db_session, spec_set=True, instance=True
        )
        return pyramid_request

    @pytest.fixture
    def hmac(self, patch):
        return patch("h.auth.util.hmac")


@pytest.fixture
def user_service(pyramid_config):
    service = mock.create_autospec(UserService, spec_set=True, instance=True)
    service.fetch.return_value = None
    pyramid_config.register_service(service, name="user")
    return service


@pytest.fixture
def auth_client(factories):
    return factories.ConfidentialAuthClient(
        authority="weylandindustries.com", grant_type=GrantType.client_credentials
    )


@pytest.fixture
def principals_for_user(patch):
    return patch("h.auth.util.principals_for_user")


@pytest.fixture
def principals_for_auth_client(patch):
    return patch("h.auth.util.principals_for_auth_client")
