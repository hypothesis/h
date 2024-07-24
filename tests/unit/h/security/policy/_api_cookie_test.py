from unittest.mock import create_autospec, sentinel

import pytest

from h.security.policy._api_cookie import APICookiePolicy
from h.security.policy._cookie import CookiePolicy


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

    def test_identity(self, api_cookie_policy, cookie_policy, pyramid_request):
        identity = api_cookie_policy.identity(pyramid_request)

        cookie_policy.identity.assert_called_once_with(pyramid_request)
        assert identity == cookie_policy.identity.return_value

    def test_authenticated_userid(
        self, api_cookie_policy, cookie_policy, pyramid_request
    ):
        authenticated_userid = api_cookie_policy.authenticated_userid(pyramid_request)

        cookie_policy.authenticated_userid.assert_called_once_with(pyramid_request)
        assert authenticated_userid == cookie_policy.authenticated_userid.return_value

    def test_permits(self, api_cookie_policy, cookie_policy, pyramid_request):
        permits = api_cookie_policy.permits(
            pyramid_request, sentinel.context, sentinel.permission
        )

        cookie_policy.permits.assert_called_once_with(
            pyramid_request, sentinel.context, sentinel.permission
        )
        assert permits == cookie_policy.permits.return_value

    @pytest.fixture
    def cookie_policy(self):
        return create_autospec(CookiePolicy, instance=True, spec_set=True)

    @pytest.fixture
    def api_cookie_policy(self, cookie_policy):
        return APICookiePolicy(cookie_policy)
