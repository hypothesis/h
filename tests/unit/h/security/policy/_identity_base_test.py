from unittest.mock import sentinel

import pytest

from h.security import Identity
from h.security.policy._identity_base import IdentityBasedPolicy


class TestIdentityBasedPolicy:
    def test_identity_method_does_nothing(self, pyramid_request):
        assert IdentityBasedPolicy().identity(pyramid_request) is None

    def test_permits(self, policy, identity, pyramid_request, identity_permits):
        result = policy.permits(pyramid_request, sentinel.context, sentinel.permission)

        identity_permits.assert_called_once_with(
            identity, sentinel.context, sentinel.permission
        )
        assert result == identity_permits.return_value

    def test_authenticated_userid(self, policy, pyramid_request, identity):
        assert policy.authenticated_userid(pyramid_request) == identity.user.userid

    def test_authenticated_userid_return_None_if_the_identity_has_no_user(
        self, policy, pyramid_request, identity
    ):
        identity.user = None

        assert policy.authenticated_userid(pyramid_request) is None

    def test_authenticated_userid_return_None_if_the_identity_is_None(
        self, policy, pyramid_request
    ):
        policy.returned_identity = None

        assert policy.authenticated_userid(pyramid_request) is None

    def test_remember_does_nothing(self, policy, pyramid_request):
        assert policy.remember(pyramid_request, "foo") == []

    def test_forget_does_nothing(self, policy, pyramid_request):
        assert policy.forget(pyramid_request) == []

    @pytest.fixture
    def identity(self, factories):
        return Identity.from_models(user=factories.User())

    @pytest.fixture
    def policy(self, identity):
        class CustomPolicy(IdentityBasedPolicy):
            returned_identity = None

            def identity(self, _request):
                return self.returned_identity

        policy = CustomPolicy()
        policy.returned_identity = identity

        return policy

    @pytest.fixture(autouse=True)
    def identity_permits(self, patch):
        return patch("h.security.policy._identity_base.identity_permits")
