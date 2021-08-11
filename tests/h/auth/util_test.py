from unittest import mock

import pytest
import sqlalchemy as sa

from h.auth import util
from h.models import AuthClient
from h.models.auth_client import GrantType


class TestClientAuthority:
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


class TestAuthDomain:
    def test_it_returns_the_request_domain_if_authority_isnt_set(self, pyramid_request):
        # Make sure h.authority isn't set.
        pyramid_request.registry.settings.pop("h.authority", None)

        assert util.default_authority(pyramid_request) == pyramid_request.domain

    def test_it_allows_overriding_request_domain(self, pyramid_request):
        pyramid_request.registry.settings["h.authority"] = "foo.org"
        assert util.default_authority(pyramid_request) == "foo.org"

    def test_it_returns_str(self, pyramid_request):
        pyramid_request.domain = str(pyramid_request.domain)
        assert isinstance(util.default_authority(pyramid_request), str)


class TestVerifyAuthClient:
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
def auth_client(factories):
    return factories.ConfidentialAuthClient(
        authority="weylandindustries.com", grant_type=GrantType.client_credentials
    )
