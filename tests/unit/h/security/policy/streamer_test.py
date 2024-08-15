from unittest.mock import sentinel

import pytest

from h.security.policy.streamer import StreamerPolicy


class TestStreamerPolicy:
    def test_forget(self, streamer_policy, pyramid_request):
        assert streamer_policy.forget(pyramid_request, foo="bar") == []

    def test_identity(self, bearer_token_policy, streamer_policy, pyramid_request):
        identity = streamer_policy.identity(pyramid_request)

        bearer_token_policy.identity.assert_called_once_with(pyramid_request)
        assert identity == bearer_token_policy.identity.return_value

    def test_authenticated_userid(
        self, bearer_token_policy, streamer_policy, pyramid_request, Identity
    ):
        authenticated_userid = streamer_policy.authenticated_userid(pyramid_request)

        bearer_token_policy.identity.assert_called_once_with(pyramid_request)
        Identity.authenticated_userid.assert_called_once_with(
            bearer_token_policy.identity.return_value
        )
        assert authenticated_userid == Identity.authenticated_userid.return_value

    def test_remember(self, streamer_policy, pyramid_request):
        assert (
            streamer_policy.remember(pyramid_request, sentinel.userid, foo="bar") == []
        )

    def test_permits(
        self, bearer_token_policy, streamer_policy, identity_permits, pyramid_request
    ):
        permits = streamer_policy.permits(
            pyramid_request, sentinel.context, sentinel.permission
        )

        bearer_token_policy.identity.assert_called_once_with(pyramid_request)
        identity_permits.assert_called_once_with(
            bearer_token_policy.identity.return_value,
            sentinel.context,
            sentinel.permission,
        )
        assert permits == identity_permits.return_value

    @pytest.fixture
    def streamer_policy(self):
        return StreamerPolicy()


@pytest.fixture
def bearer_token_policy(BearerTokenPolicy):
    return BearerTokenPolicy.return_value


@pytest.fixture(autouse=True)
def BearerTokenPolicy(mocker):
    return mocker.patch(
        "h.security.policy.streamer.BearerTokenPolicy", autospec=True, spec_set=True
    )


@pytest.fixture(autouse=True)
def Identity(mocker):
    return mocker.patch(
        "h.security.policy.streamer.Identity", autospec=True, spec_set=True
    )


@pytest.fixture(autouse=True)
def identity_permits(mocker):
    return mocker.patch(
        "h.security.policy.streamer.identity_permits", autospec=True, spec_set=True
    )
