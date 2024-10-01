from unittest.mock import create_autospec, sentinel

import pytest
from pyramid.csrf import SessionCSRFStoragePolicy
from pyramid.exceptions import BadCSRFOrigin, BadCSRFToken

from h.security.identity import Identity as Identity_
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
        self, pyramid_csrf_request, route_name, request_method, expected_result
    ):
        pyramid_csrf_request.matched_route.name = route_name
        pyramid_csrf_request.method = request_method

        assert APICookiePolicy.handles(pyramid_csrf_request) == expected_result

    def test_identity(self, api_cookie_policy, helper, pyramid_csrf_request):
        identity = api_cookie_policy.identity(pyramid_csrf_request)

        helper.add_vary_by_cookie.assert_called_once_with(pyramid_csrf_request)
        helper.identity.assert_called_once_with(sentinel.cookie, pyramid_csrf_request)
        assert identity == helper.identity.return_value[0]

    def test_identity_with_no_auth_cookie(
        self, api_cookie_policy, helper, pyramid_request
    ):
        helper.identity.return_value = (None, None)

        assert api_cookie_policy.identity(pyramid_request) is None

    def test_identity_with_wrong_origin(self, api_cookie_policy, pyramid_csrf_request):
        pyramid_csrf_request.referrer = "https://evil.com"

        with pytest.raises(BadCSRFOrigin):
            api_cookie_policy.identity(pyramid_csrf_request)

    def test_identity_with_wrong_csrf_token(
        self, api_cookie_policy, pyramid_csrf_request
    ):
        del pyramid_csrf_request.headers["X-CSRF-Token"]

        with pytest.raises(BadCSRFToken):
            api_cookie_policy.identity(pyramid_csrf_request)

    @pytest.fixture
    def helper(self, factories):
        helper = create_autospec(AuthTicketCookieHelper, instance=True, spec_set=True)
        helper.identity.return_value = (
            create_autospec(Identity_, instance=True, spec_set=True),
            factories.AuthTicket(),
        )
        return helper

    @pytest.fixture
    def api_cookie_policy(self, helper):
        return APICookiePolicy(sentinel.cookie, helper)


@pytest.fixture(autouse=True)
def Identity(mocker):
    return mocker.patch(
        "h.security.policy._api_cookie.Identity", autospec=True, spec_set=True
    )


@pytest.fixture(autouse=True)
def pyramid_config(pyramid_config):
    pyramid_config.set_csrf_storage_policy(SessionCSRFStoragePolicy())
    return pyramid_config
