import pytest

from h.auth.policy._identity_base import IdentityBasedPolicy
from h.security import Identity


class TestIdentityBasedPolicy:
    def test_identity_method_does_nothing(self, pyramid_request):
        assert IdentityBasedPolicy().identity(pyramid_request) is None

    @pytest.mark.parametrize(
        "method", ("authenticated_userid", "unauthenticated_userid")
    )
    def test_userid_methods(self, policy, pyramid_request, identity, method):
        assert getattr(policy, method)(pyramid_request) == identity.user.userid

    @pytest.mark.parametrize(
        "method", ("authenticated_userid", "unauthenticated_userid")
    )
    def test_userid_methods_return_None_if_the_identity_has_no_user(
        self, policy, pyramid_request, identity, method
    ):
        identity.user = None

        assert getattr(policy, method)(pyramid_request) is None

    @pytest.mark.parametrize(
        "method", ("authenticated_userid", "unauthenticated_userid")
    )
    def test_userid_methods_return_None_if_the_identity_is_None(
        self, policy, pyramid_request, method
    ):
        policy.returned_identity = None

        assert getattr(policy, method)(pyramid_request) is None

    def test_effective_principals(
        self, policy, pyramid_request, identity, principals_for_identity
    ):
        principals = policy.effective_principals(pyramid_request)

        principals_for_identity.assert_called_once_with(identity)
        assert principals == principals_for_identity.return_value

    def test_remember_does_nothing(self, policy, pyramid_request):
        assert policy.remember(pyramid_request, "foo") == []

    def test_forget_does_nothing(self, policy, pyramid_request):
        assert policy.forget(pyramid_request) == []

    @pytest.fixture
    def identity(self, factories):
        return Identity(user=factories.User())

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
    def principals_for_identity(self, patch):
        return patch("h.auth.policy._identity_base.principals_for_identity")
