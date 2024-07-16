from unittest.mock import create_autospec, sentinel

import pytest

from h.security.policy import SecurityPolicy
from h.security.policy.combined import applicable_policies, call_policies


class TestSecurityPolicy:
    def test_remember(self, call_policies, policy, pyramid_request):
        headers = policy.remember(pyramid_request, sentinel.userid, foo=sentinel.foo)

        call_policies.assert_called_once_with(
            "remember", [], pyramid_request, sentinel.userid, foo=sentinel.foo
        )
        assert headers == call_policies.return_value

    def test_forget(self, call_policies, policy, pyramid_request):
        headers = policy.forget(pyramid_request, foo=sentinel.foo)

        call_policies.assert_called_once_with(
            "forget", [], pyramid_request, foo=sentinel.foo
        )
        assert headers == call_policies.return_value

    def test_identity(self, call_policies, policy, pyramid_request):
        identity = policy.identity(pyramid_request)

        call_policies.assert_called_once_with("identity", None, pyramid_request)
        assert identity == call_policies.return_value

    @pytest.fixture
    def policy(self):
        return SecurityPolicy()

    @pytest.fixture(autouse=True)
    def call_policies(self, mocker):
        return mocker.patch("h.security.policy.combined.call_policies")


class TestCallPolicies:
    def test_call_policies_when_first_policy_returns_truthy(
        self,
        applicable_policies,
        policies,
        policy_classes,
        pyramid_request,
    ):
        # The first policy returns truthy.
        policies[0].method.return_value = True

        result = call_policies(
            "method", sentinel.fallback, pyramid_request, "arg", kwarg="kwarg"
        )

        applicable_policies.assert_called_once_with(pyramid_request, policy_classes)
        # It just returns the truthy result from the first policy,
        # and doesn't even call the second policy.
        policies[0].method.assert_called_once_with(
            pyramid_request, "arg", kwarg="kwarg"
        )
        policies[1].method.assert_not_called()
        # It doesn't even instantiate the second policy.
        applicable_policies.return_value[1].assert_not_called()
        assert result == policies[0].method.return_value

    def test_call_policies_when_second_policy_returns_truthy(
        self, applicable_policies, policies, policy_classes, pyramid_request
    ):
        # The first policy returns falsey but the second policy returns truthy.
        policies[0].method.return_value = False
        policies[1].method.return_value = True

        result = call_policies(
            "method", sentinel.fallback, pyramid_request, "arg", kwarg="kwarg"
        )

        applicable_policies.assert_called_once_with(pyramid_request, policy_classes)
        # It calls both policies and returns the truthy result from the second policy.
        policies[0].method.assert_called_once_with(
            pyramid_request, "arg", kwarg="kwarg"
        )
        policies[1].method.assert_called_once_with(
            pyramid_request, "arg", kwarg="kwarg"
        )
        assert result == policies[1].method.return_value

    def test_call_policies_when_all_policies_return_falsey(
        self, applicable_policies, policies, policy_classes, pyramid_request
    ):
        # Both policies return falsey.
        policies[0].method.return_value = False
        policies[1].method.return_value = False

        result = call_policies(
            "method", sentinel.fallback, pyramid_request, "arg", kwarg="kwarg"
        )

        applicable_policies.assert_called_once_with(pyramid_request, policy_classes)
        # It calls all policies and returns the falsey result from the last policy.
        policies[0].method.assert_called_once_with(
            pyramid_request, "arg", kwarg="kwarg"
        )
        policies[1].method.assert_called_once_with(
            pyramid_request, "arg", kwarg="kwarg"
        )
        assert result == sentinel.fallback

    def test_call_policies_when_there_are_no_applicable_policies(
        self, applicable_policies, pyramid_request
    ):
        applicable_policies.return_value = []

        result = call_policies("method", sentinel.fallback, pyramid_request)

        assert result == sentinel.fallback

    @pytest.fixture
    def policy_classes(
        self, RemoteUserPolicy, CookiePolicy, BearerTokenPolicy, AuthClientPolicy
    ):
        return [RemoteUserPolicy, CookiePolicy, BearerTokenPolicy, AuthClientPolicy]

    @pytest.fixture(autouse=True)
    def applicable_policies(self, mocker, CookiePolicy, BearerTokenPolicy):
        return mocker.patch(
            "h.security.policy.combined.applicable_policies",
            return_value=[CookiePolicy, BearerTokenPolicy],
        )

    @pytest.fixture
    def policies(self, applicable_policies):
        return [
            policy_class.return_value
            for policy_class in applicable_policies.return_value
        ]

    @pytest.fixture(autouse=True)
    def AuthClientPolicy(self, mocker):
        return mocker.patch("h.security.policy.combined.AuthClientPolicy")

    @pytest.fixture(autouse=True)
    def BearerTokenPolicy(self, mocker):
        return mocker.patch("h.security.policy.combined.BearerTokenPolicy")

    @pytest.fixture(autouse=True)
    def CookiePolicy(self, mocker):
        return mocker.patch("h.security.policy.combined.CookiePolicy")

    @pytest.fixture(autouse=True)
    def RemoteUserPolicy(self, mocker):
        return mocker.patch("h.security.policy.combined.RemoteUserPolicy")


class TestApplicablePolicies:
    @pytest.mark.parametrize(
        "return_values,expected_policies",
        [
            ([True, True], [0, 1]),
            ([False, True], [1]),
            ([True, False], [0]),
            ([False, False], []),
        ],
    )
    def test_applicable_policies(
        self, return_values, expected_policies, pyramid_request
    ):
        class Spec:
            @staticmethod
            def handles(request) -> bool:
                """Return True if this policy can handle `request`."""

        policies = [
            create_autospec(Spec, spec_set=True),
            create_autospec(Spec, spec_set=True),
        ]
        for policy, return_value in zip(policies, return_values):
            policy.handles.return_value = return_value

        returned_policies = applicable_policies(pyramid_request, policies)

        for policy in policies:
            policy.handles.assert_called_once_with(pyramid_request)
        assert returned_policies == [policies[index] for index in expected_policies]
