from unittest.mock import create_autospec, sentinel

import pytest
from pyramid.request import Request

from h.security.policy._api import APIPolicy, applicable_policies


class TestAPIPolicy:
    def test_forget(self, api_policy, pyramid_request):
        assert api_policy.forget(pyramid_request, foo="bar") == []

    def test_identity_when_first_sub_policy_returns_truthy(
        self, applicable_policies, api_policy, pyramid_request
    ):
        applicable_policies.return_value[0].identity.return_value = True
        applicable_policies.return_value[1].identity.return_value = False

        identity = api_policy.identity(pyramid_request)

        applicable_policies.assert_called_once_with(
            pyramid_request, sentinel.sub_policies
        )
        applicable_policies.return_value[0].identity.assert_called_once_with(
            pyramid_request
        )
        applicable_policies.return_value[1].identity.assert_not_called()
        assert identity == applicable_policies.return_value[0].identity.return_value

    def test_identity_when_second_sub_policy_returns_truthy(
        self, applicable_policies, api_policy, pyramid_request
    ):
        applicable_policies.return_value[0].identity.return_value = False
        applicable_policies.return_value[1].identity.return_value = True

        identity = api_policy.identity(pyramid_request)

        applicable_policies.return_value[1].identity.assert_called_once_with(
            pyramid_request
        )
        assert identity == applicable_policies.return_value[1].identity.return_value

    def test_identity_when_all_sub_policies_return_falsey(
        self, applicable_policies, api_policy, pyramid_request
    ):
        applicable_policies.return_value[0].identity.return_value = False
        applicable_policies.return_value[1].identity.return_value = False

        identity = api_policy.identity(pyramid_request)

        assert identity is None

    def test_identity_when_there_are_no_applicable_policies(
        self, applicable_policies, api_policy, pyramid_request
    ):
        applicable_policies.return_value = []

        identity = api_policy.identity(pyramid_request)

        assert identity is None

    def test_authenticated_userid(self, api_policy, pyramid_request, Identity, mocker):
        mocker.spy(api_policy, "identity")

        authenticated_userid = api_policy.authenticated_userid(pyramid_request)

        api_policy.identity.assert_called_once_with(pyramid_request)
        Identity.authenticated_userid.assert_called_once_with(
            api_policy.identity.spy_return
        )
        assert authenticated_userid == Identity.authenticated_userid.return_value

    def test_remember(self, api_policy, pyramid_request):
        assert api_policy.remember(pyramid_request, sentinel.userid, foo="bar") == []

    def test_permits(self, api_policy, pyramid_request, identity_permits, mocker):
        mocker.spy(api_policy, "identity")

        result = api_policy.permits(
            pyramid_request, sentinel.context, sentinel.permission
        )

        api_policy.identity.assert_called_once_with(pyramid_request)
        identity_permits.assert_called_once_with(
            api_policy.identity.spy_return, sentinel.context, sentinel.permission
        )
        assert result == identity_permits.return_value

    @pytest.fixture(autouse=True)
    def applicable_policies(self, mocker):
        class SubpolicySpec:
            def identity(self, request: Request):
                """Return the identity of the current user."""

        return mocker.patch(
            "h.security.policy._api.applicable_policies",
            return_value=[
                create_autospec(SubpolicySpec, instance=True, spec_set=True),
                create_autospec(SubpolicySpec, instance=True, spec_set=True),
            ],
        )

    @pytest.fixture
    def api_policy(self):
        return APIPolicy(sentinel.sub_policies)


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


@pytest.fixture(autouse=True)
def Identity(mocker):
    return mocker.patch("h.security.policy._api.Identity", autospec=True, spec_set=True)


@pytest.fixture(autouse=True)
def identity_permits(mocker):
    return mocker.patch(
        "h.security.policy._api.identity_permits", autospec=True, spec_set=True
    )
