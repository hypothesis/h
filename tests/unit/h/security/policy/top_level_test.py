from unittest.mock import patch, sentinel

import pytest

from h.security.policy import TopLevelPolicy

# pylint: disable=protected-access


class TestTopLevelPolicy:
    def test_construction(self, BearerTokenPolicy, AuthClientPolicy, CookiePolicy):
        policy = TopLevelPolicy(proxy_auth=False)

        BearerTokenPolicy.assert_called_once_with()
        assert policy._bearer_token_policy == BearerTokenPolicy.return_value
        AuthClientPolicy.assert_called_once_with()
        assert policy._http_basic_auth_policy == AuthClientPolicy.return_value
        CookiePolicy.assert_called_once_with()
        assert policy._ui_policy == CookiePolicy.return_value

    def test_construction_for_proxy_auth(self, RemoteUserPolicy):
        policy = TopLevelPolicy(proxy_auth=True)

        RemoteUserPolicy.assert_called_once_with()
        assert policy._ui_policy == RemoteUserPolicy.return_value

    @pytest.mark.parametrize(
        "method,args,kwargs",
        (
            ("remember", [sentinel.userid], {"kwargs": True}),
            ("forget", [], {}),
            ("identity", [], {}),
        ),
    )
    def test_most_methods_delegate(self, pyramid_request, method, args, kwargs):
        policy = TopLevelPolicy()

        with patch.object(policy, "_call_sub_policies") as _call_sub_policies:
            auth_method = getattr(policy, method)

            result = auth_method(pyramid_request, *args, **kwargs)

            _call_sub_policies.assert_called_once_with(
                method, pyramid_request, *args, **kwargs
            )
            assert result == _call_sub_policies.return_value

    def test_identity_caches(self, pyramid_request, CookiePolicy):
        policy = TopLevelPolicy()

        policy.identity(pyramid_request)
        policy.identity(pyramid_request)

        CookiePolicy.return_value.identity.assert_called_once()

    @pytest.mark.parametrize("method,args", (("remember", ["userid"]), ("forget", [])))
    def test_remember_and_forget_reset_cache(
        self, pyramid_request, CookiePolicy, method, args
    ):
        policy = TopLevelPolicy()

        policy.identity(pyramid_request)
        getattr(policy, method)(pyramid_request, *args)
        policy.identity(pyramid_request)

        assert CookiePolicy.return_value.identity.call_count == 2

    @pytest.mark.parametrize(
        "route_name,is_ui",
        (
            ("anything", True),
            ("api.anything", False),
        ),
    )
    def test_calls_are_routed_based_on_api_or_not(
        self, pyramid_request, route_name, is_ui
    ):
        pyramid_request.matched_route.name = route_name
        policy = TopLevelPolicy()

        # Use `remember()` as an example, we've proven above which methods use
        # this
        result = policy.remember(pyramid_request, sentinel.userid, kwarg=True)

        if is_ui:
            called_policy, uncalled_policy = (
                policy._ui_policy,
                policy._bearer_token_policy,
            )
        else:
            called_policy, uncalled_policy = (
                policy._bearer_token_policy,
                policy._ui_policy,
            )

        called_policy.remember.assert_called_once_with(  # pylint:disable=no-member
            pyramid_request, sentinel.userid, kwarg=True
        )
        assert result == called_policy.remember.return_value  # pylint:disable=no-member

        uncalled_policy.remember.assert_not_called()  # pylint:disable=no-member

    @pytest.mark.parametrize("bearer_returns", (True, False))
    @pytest.mark.parametrize("basic_auth_handles", (True, False))
    def test_api_calls_are_passed_on(
        self, pyramid_request, bearer_returns, basic_auth_handles
    ):
        # Pick a URL instead of retesting which URLs trigger the API behavior
        pyramid_request.matched_route.name = "api.anything"
        policy = TopLevelPolicy()
        policy._bearer_token_policy.remember.return_value = bearer_returns
        policy._http_basic_auth_policy.handles.return_value = basic_auth_handles

        result = policy.remember(pyramid_request, sentinel.userid, kwarg=True)

        if not bearer_returns:
            policy._http_basic_auth_policy.handles.assert_called_once_with(
                pyramid_request
            )

        if basic_auth_handles and not bearer_returns:
            policy._http_basic_auth_policy.remember.assert_called_once_with(  # pylint:disable=no-member
                pyramid_request, sentinel.userid, kwarg=True
            )
            assert (
                result
                == policy._http_basic_auth_policy.remember.return_value  # pylint:disable=no-member
            )
        else:
            policy._http_basic_auth_policy.remember.assert_not_called()  # pylint:disable=no-member
            assert (
                result
                == policy._bearer_token_policy.remember.return_value  # pylint:disable=no-member
            )

    @pytest.fixture(autouse=True)
    def BearerTokenPolicy(self, patch):
        return patch("h.security.policy.top_level.BearerTokenPolicy")

    @pytest.fixture(autouse=True)
    def AuthClientPolicy(self, patch):
        return patch("h.security.policy.top_level.AuthClientPolicy")

    @pytest.fixture(autouse=True)
    def RemoteUserPolicy(self, patch):
        return patch("h.security.policy.top_level.RemoteUserPolicy")

    @pytest.fixture(autouse=True)
    def CookiePolicy(self, patch):
        return patch("h.security.policy.top_level.CookiePolicy")
