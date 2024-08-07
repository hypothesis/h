from unittest.mock import create_autospec, sentinel

import pytest

from h.security.policy._api_cookie import APICookiePolicy
from h.security.policy.helpers import AuthTicketCookieHelper


class TestAPICookiePolicy:
    @pytest.mark.parametrize(
        "route_name,request_method,expected_result",
        [
            ("api.groups", "POST", True),
            ("api.group", "PATCH", True),
            ("api.group", "DELETE", False),
            ("anything", "POST", False),
        ],
    )
    def test_handles(
        self, pyramid_request, route_name, request_method, expected_result
    ):
        pyramid_request.matched_route.name = route_name
        pyramid_request.method = request_method

        assert APICookiePolicy.handles(pyramid_request) == expected_result

    def test_identity(self, api_cookie_policy, helper, pyramid_request):
        identity = api_cookie_policy.identity(pyramid_request)

        helper.add_vary_by_cookie.assert_called_once_with(pyramid_request)
        helper.identity.assert_called_once_with(sentinel.cookie, pyramid_request)
        assert identity == helper.identity.return_value

    def test_authenticated_userid(
        self, api_cookie_policy, helper, pyramid_request, Identity
    ):
        authenticated_userid = api_cookie_policy.authenticated_userid(pyramid_request)

        helper.add_vary_by_cookie.assert_called_once_with(pyramid_request)
        helper.identity.assert_called_once_with(sentinel.cookie, pyramid_request)
        Identity.authenticated_userid.assert_called_once_with(
            helper.identity.return_value
        )
        assert authenticated_userid == Identity.authenticated_userid.return_value

    def test_permits(
        self, api_cookie_policy, helper, pyramid_request, identity_permits
    ):
        permits = api_cookie_policy.permits(
            pyramid_request, sentinel.context, sentinel.permission
        )

        helper.add_vary_by_cookie.assert_called_once_with(pyramid_request)
        helper.identity.assert_called_once_with(sentinel.cookie, pyramid_request)
        identity_permits.assert_called_once_with(
            helper.identity.return_value, sentinel.context, sentinel.permission
        )
        assert permits == identity_permits.return_value

    @pytest.fixture
    def helper(self):
        return create_autospec(AuthTicketCookieHelper, instance=True, spec_set=True)

    @pytest.fixture
    def api_cookie_policy(self, helper):
        return APICookiePolicy(sentinel.cookie, helper)


@pytest.fixture(autouse=True)
def Identity(mocker):
    return mocker.patch(
        "h.security.policy._api_cookie.Identity", autospec=True, spec_set=True
    )


@pytest.fixture(autouse=True)
def identity_permits(mocker):
    return mocker.patch(
        "h.security.policy._api_cookie.identity_permits", autospec=True, spec_set=True
    )
