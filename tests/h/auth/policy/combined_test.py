from unittest.mock import patch, sentinel

import pytest

from h.auth.policy.combined import AuthenticationPolicy

# pylint: disable=protected-access


class TestAuthenticationPolicy:
    def test_construction(
        self, TokenAuthenticationPolicy, AuthClientPolicy, CookieAuthenticationPolicy
    ):
        policy = AuthenticationPolicy(proxy_auth=False)

        TokenAuthenticationPolicy.assert_called_once_with()
        assert policy._bearer_token_policy == TokenAuthenticationPolicy.return_value
        AuthClientPolicy.assert_called_once_with()
        assert policy._http_basic_auth_policy == AuthClientPolicy.return_value
        CookieAuthenticationPolicy.assert_called_once_with()
        assert policy._ui_policy == CookieAuthenticationPolicy.return_value

    def test_construction_for_proxy_auth(self, RemoteUserAuthenticationPolicy):
        policy = AuthenticationPolicy(proxy_auth=True)

        RemoteUserAuthenticationPolicy.assert_called_once_with()
        assert policy._ui_policy == RemoteUserAuthenticationPolicy.return_value

    @pytest.mark.parametrize(
        "method,args,kwargs",
        (
            ("authenticated_userid", [], {}),
            ("unauthenticated_userid", [], {}),
            ("remember", [sentinel.userid], {"kwargs": True}),
            ("forget", [], {}),
            ("identity", [], {}),
        ),
    )
    def test_most_methods_delegate(self, pyramid_request, method, args, kwargs):
        policy = AuthenticationPolicy()

        with patch.object(policy, "_call_sub_policies") as _call_sub_policies:
            auth_method = getattr(policy, method)

            result = auth_method(pyramid_request, *args, **kwargs)

            _call_sub_policies.assert_called_once_with(
                method, pyramid_request, *args, **kwargs
            )
            assert result == _call_sub_policies.return_value

    @pytest.mark.parametrize(
        "path,is_ui",
        (
            ("/most/things/really", True),
            ("/api/token", True),
            ("/api/badge", True),
            ("/api/anything_else", False),
        ),
    )
    def test_calls_are_routed_based_on_api_or_not(self, pyramid_request, path, is_ui):
        pyramid_request.path = path
        policy = AuthenticationPolicy()

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

        called_policy.remember.assert_called_once_with(
            pyramid_request, sentinel.userid, kwarg=True
        )
        assert result == called_policy.remember.return_value

        uncalled_policy.remember.assert_not_called()

    @pytest.mark.parametrize("bearer_returns", (True, False))
    @pytest.mark.parametrize("basic_auth_handles", (True, False))
    def test_api_calls_are_passed_on(
        self, pyramid_request, bearer_returns, basic_auth_handles
    ):
        # Pick a URL instead of retesting which URLs trigger the API behavior
        pyramid_request.path = "/api/anything"
        policy = AuthenticationPolicy()
        policy._bearer_token_policy.remember.return_value = bearer_returns
        policy._http_basic_auth_policy.handles.return_value = basic_auth_handles

        result = policy.remember(pyramid_request, sentinel.userid, kwarg=True)

        if not bearer_returns:
            policy._http_basic_auth_policy.handles.assert_called_once_with(
                pyramid_request
            )

        if basic_auth_handles and not bearer_returns:
            policy._http_basic_auth_policy.remember.assert_called_once_with(
                pyramid_request, sentinel.userid, kwarg=True
            )
            assert result == policy._http_basic_auth_policy.remember.return_value
        else:
            policy._http_basic_auth_policy.remember.assert_not_called()
            assert result == policy._bearer_token_policy.remember.return_value

    @pytest.fixture(autouse=True)
    def TokenAuthenticationPolicy(self, patch):
        return patch("h.auth.policy.combined.TokenAuthenticationPolicy")

    @pytest.fixture(autouse=True)
    def AuthClientPolicy(self, patch):
        return patch("h.auth.policy.combined.AuthClientPolicy")

    @pytest.fixture(autouse=True)
    def RemoteUserAuthenticationPolicy(self, patch):
        return patch("h.auth.policy.combined.RemoteUserAuthenticationPolicy")

    @pytest.fixture(autouse=True)
    def CookieAuthenticationPolicy(self, patch):
        return patch("h.auth.policy.combined.CookieAuthenticationPolicy")
