from datetime import timedelta
from unittest.mock import MagicMock, call, sentinel
from urllib.parse import urlencode, urlunparse

import pytest
from pyramid.httpexceptions import HTTPForbidden, HTTPFound

from h.models.user_identity import IdentityProvider
from h.schemas import ValidationError
from h.schemas.oauth import InvalidOAuth2StateParamError
from h.services.exceptions import ExternalRequestError
from h.services.jwt import JWTAudiences, JWTDecodeError, JWTIssuers
from h.views.exceptions import UnexpectedRouteError
from h.views.oidc import (
    STATE_SESSION_KEY_FMT,
    AccessDeniedError,
    OIDCState,
    SSOConnectAndLoginViews,
    SSORedirectViews,
    UnexpectedActionError,
    UserConflictError,
    handle_external_request_error,
)


@pytest.mark.usefixtures("jwt_service")
class TestSSOConnectAndLoginViews:
    @pytest.mark.parametrize(
        "route_name,expected_action",
        [
            ("oidc.connect.orcid", "connect"),
            ("oidc.login.orcid", "login"),
        ],
    )
    def test_connect_or_login(
        self, pyramid_request, route_name, expected_action, jwt_service, secrets
    ):
        pyramid_request.matched_route.name = route_name

        result = SSOConnectAndLoginViews(pyramid_request).connect_or_login()

        secrets.token_hex.assert_called_once_with()
        jwt_service.encode_symmetric.assert_called_once_with(
            OIDCState(action=expected_action, rfp=secrets.token_hex.return_value),
            expires_in=timedelta(hours=1),
            issuer=JWTIssuers.OIDC_CONNECT_OR_LOGIN_ORCID,
            audience=JWTAudiences.OIDC_REDIRECT_ORCID,
        )
        assert (
            pyramid_request.session[STATE_SESSION_KEY_FMT.format(provider="orcid")]
            == jwt_service.encode_symmetric.return_value
        )
        assert result.location == urlunparse(
            (
                "https",
                "sandbox.orcid.org",
                "/authorize",
                "",
                urlencode(
                    {
                        "client_id": sentinel.client_id,
                        "response_type": "code",
                        "redirect_uri": pyramid_request.route_url(
                            "oidc.redirect.orcid"
                        ),
                        "state": jwt_service.encode_symmetric.return_value,
                        "scope": "openid",
                    }
                ),
                "",
            )
        )

    def test_connect_or_login_with_unexpected_route_name(self, pyramid_request):
        pyramid_request.matched_route.name = "unexpected"

        with pytest.raises(UnexpectedRouteError, match="^unexpected$"):
            SSOConnectAndLoginViews(pyramid_request).connect_or_login()

    def test_notfound(self, pyramid_request):
        pyramid_request.user = None

        result = SSOConnectAndLoginViews(pyramid_request).notfound()

        assert result == {}

    def test_login_already_authenticated(self, pyramid_request, matchers):
        response = SSOConnectAndLoginViews(
            pyramid_request
        ).login_already_authenticated()

        assert response == matchers.Redirect302To(
            pyramid_request.route_url(
                "activity.user_search", username=pyramid_request.user.username
            )
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request, factories):
        pyramid_request.user = factories.User()
        pyramid_request.registry.settings.update(
            {
                "orcid_host": IdentityProvider.ORCID,
                "oidc_clientid_orcid": sentinel.client_id,
                "oidc_clientsecret_orcid": sentinel.client_secret,
                "oidc_authorizationurl_orcid": "https://sandbox.orcid.org/authorize",
            }
        )
        return pyramid_request

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("oidc.connect.orcid", "/oidc/connect/orcid")
        pyramid_config.add_route("oidc.redirect.orcid", "/oidc/redirect/orcid")
        pyramid_config.add_route("activity.user_search", "/users/{username}")


@pytest.mark.usefixtures("oidc_service", "user_service", "jwt_service")
class TestSSORedirectViews:
    @pytest.mark.usefixtures(
        "with_both_connect_and_login_actions",
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
        "assert_no_success_message_was_flashed",
    )
    def test_redirect_when_theres_no_state_in_the_session(self, pyramid_request, views):
        del pyramid_request.session[STATE_SESSION_KEY_FMT.format(provider="orcid")]

        with pytest.raises(InvalidOAuth2StateParamError):
            views.redirect()

    @pytest.mark.usefixtures(
        "with_both_connect_and_login_actions",
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
        "assert_no_success_message_was_flashed",
    )
    def test_redirect_with_unexpected_route_name(self, pyramid_request, views):
        pyramid_request.matched_route.name = "unexpected"

        with pytest.raises(UnexpectedRouteError, match="^unexpected$"):
            views.redirect()

    @pytest.mark.usefixtures("with_both_connect_and_login_actions")
    def test_redirect_validates_the_request_params(
        self, pyramid_request, views, OAuth2RedirectSchema
    ):
        views.redirect()

        OAuth2RedirectSchema.validate.assert_called_once_with(
            pyramid_request.params, sentinel.state
        )

    @pytest.mark.usefixtures(
        "with_both_connect_and_login_actions",
        "assert_state_removed_from_session",
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
        "assert_no_success_message_was_flashed",
    )
    @pytest.mark.parametrize(
        "params,expected_exception_class",
        [
            ({"error": "access_denied"}, AccessDeniedError),
            ({"error": "something_else"}, ValidationError),
            ({}, ValidationError),
        ],
    )
    def test_redirect_when_validation_error(
        self,
        pyramid_request,
        views,
        OAuth2RedirectSchema,
        params,
        expected_exception_class,
    ):
        OAuth2RedirectSchema.validate.side_effect = ValidationError()
        pyramid_request.params = params

        with pytest.raises(expected_exception_class) as exc_info:
            views.redirect()

        assert OAuth2RedirectSchema.validate.side_effect in [
            exc_info.value,
            exc_info.value.__cause__,
        ]

    @pytest.mark.usefixtures(
        "with_both_connect_and_login_actions",
        "assert_state_removed_from_session",
        "assert_state_param_decoded_correctly",
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
        "assert_no_success_message_was_flashed",
    )
    def test_redirect_if_state_jwt_fails_to_decode(self, views, jwt_service):
        jwt_service.decode_symmetric.side_effect = JWTDecodeError

        with pytest.raises(JWTDecodeError):
            views.redirect()

    @pytest.mark.usefixtures(
        "assert_state_removed_from_session",
        "assert_state_param_decoded_correctly",
        "assert_no_account_connection_was_added",
        "assert_no_success_message_was_flashed",
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
    )
    def test_redirect_if_action_is_connect_and_user_not_authenticated(
        self, set_action, views
    ):
        set_action("connect", authenticate_user=False)

        with pytest.raises(HTTPForbidden):
            views.redirect()

    @pytest.mark.usefixtures(
        "assert_state_removed_from_session",
        "assert_state_param_decoded_correctly",
        "assert_no_success_message_was_flashed",
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
    )
    def test_redirect_if_action_is_login_and_user_authenticated(
        self, set_action, views
    ):
        set_action("login", authenticate_user=True)

        with pytest.raises(HTTPForbidden):
            views.redirect()

    @pytest.mark.usefixtures("with_both_connect_and_login_actions")
    def test_redirect_gets_the_users_orcid_id(self, views, oidc_service):
        views.redirect()

        oidc_service.get_provider_unique_id.assert_called_once_with(
            IdentityProvider.ORCID, sentinel.code
        )

    @pytest.mark.usefixtures(
        "with_both_connect_and_login_actions",
        "assert_state_removed_from_session",
        "assert_state_param_decoded_correctly",
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
        "assert_no_success_message_was_flashed",
    )
    def test_redirect_when_getting_orcid_id_fails(self, views, oidc_service):
        class TestError(Exception):
            pass

        oidc_service.get_provider_unique_id.side_effect = TestError

        with pytest.raises(TestError):
            views.redirect()

    @pytest.mark.usefixtures("with_both_connect_and_login_actions")
    def test_redirect_fetches_the_hypothesis_uiser(self, views, user_service, orcid_id):
        views.redirect()

        user_service.fetch_by_identity.assert_called_once_with(
            IdentityProvider.ORCID, orcid_id
        )

    @pytest.mark.usefixtures(
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
        "assert_no_success_message_was_flashed",
    )
    def test_redirect_with_unexpected_action(self, views, set_action):
        set_action("unexpected")

        with pytest.raises(UnexpectedActionError):
            views.redirect()

    @pytest.mark.usefixtures(
        "with_connect_action",
        "assert_state_removed_from_session",
        "assert_state_param_decoded_correctly",
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
        "assert_no_success_message_was_flashed",
    )
    def test_redirect_when_action_connect_and_a_different_account_is_already_connected(
        self, user_service, views
    ):
        user_service.fetch_by_identity.return_value = sentinel.other_user

        with pytest.raises(UserConflictError):
            views.redirect()

    @pytest.mark.usefixtures("with_connect_action")
    @pytest.mark.usefixtures(
        "assert_state_removed_from_session",
        "assert_state_param_decoded_correctly",
        "assert_success_message_was_flashed",
        "assert_user_was_not_logged_in",
    )
    def test_redirect_when_action_connect_and_account_not_yet_connected(
        self,
        pyramid_request,
        oidc_service,
        user_service,
        user,
        views,
        matchers,
        orcid_id,
    ):
        user_service.fetch_by_identity.return_value = None

        result = views.redirect()

        oidc_service.add_identity.assert_called_once_with(
            user, IdentityProvider.ORCID, orcid_id
        )
        assert result == matchers.Redirect302To(pyramid_request.route_url("account"))

    @pytest.mark.usefixtures(
        "with_connect_action",
        "assert_state_removed_from_session",
        "assert_state_param_decoded_correctly",
        "assert_success_message_was_flashed",
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
    )
    def test_redirect_when_action_connect_and_account_already_connected(
        self, pyramid_request, user_service, views, matchers
    ):
        user_service.fetch_by_identity.return_value = pyramid_request.user

        result = views.redirect()

        assert result == matchers.Redirect302To(pyramid_request.route_url("account"))

    @pytest.mark.usefixtures(
        "with_login_action",
        "assert_state_removed_from_session",
        "assert_state_param_decoded_correctly",
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
        "assert_no_success_message_was_flashed",
    )
    def test_redirect_when_action_login_and_no_connected_user_exists(
        self,
        views,
        user_service,
        pyramid_request,
        orcid_id,
        jwt_service,
        encode_idinfo_token,
    ):
        user_service.fetch_by_identity.return_value = None

        response = views.redirect()

        encode_idinfo_token.assert_called_once_with(
            jwt_service, orcid_id, JWTIssuers.OIDC_REDIRECT_ORCID
        )
        assert isinstance(response, HTTPFound)
        assert response.location == pyramid_request.route_url(
            "signup.orcid", _query=encode_idinfo_token.return_value
        )

    @pytest.mark.usefixtures(
        "with_login_action",
        "assert_state_removed_from_session",
        "assert_state_param_decoded_correctly",
        "assert_no_account_connection_was_added",
        "assert_no_success_message_was_flashed",
    )
    def test_redirect_when_action_login_and_connected_user_exists(
        self, views, login, user, pyramid_request
    ):
        login.return_value = [
            ("headername1", "headervalue1"),
            ("headername2", "headervalue2"),
        ]
        response = views.redirect()

        login.assert_called_once_with(user, pyramid_request)
        assert all(header in response.headerlist for header in login.return_value)

    def test_notfound(self, pyramid_request, views):
        result = views.notfound()

        assert pyramid_request.response.status_int == 401
        assert result == {}

    def test_invalid(self, pyramid_request, views, matchers, report_exception):
        result = views.invalid()

        report_exception.assert_called_once_with(sentinel.context)
        assert result == matchers.Redirect302To(pyramid_request.route_url("account"))
        assert pyramid_request.session.peek_flash("error") == [
            "Received an invalid redirect from ORCID!"
        ]

    def test_invalid_token(self, pyramid_request, views, matchers, report_exception):
        result = views.invalid_token()

        report_exception.assert_called_once_with(sentinel.context)
        assert result == matchers.Redirect302To(pyramid_request.route_url("account"))
        assert pyramid_request.session.peek_flash("error") == [
            "Received an invalid token from ORCID!"
        ]

    def test_denied(self, pyramid_request, views, matchers):
        result = views.denied()

        assert result == matchers.Redirect302To(pyramid_request.route_url("account"))
        assert pyramid_request.session.peek_flash("error") == [
            "The user clicked the deny button!"
        ]

    def test_external_request(
        self, pyramid_request, handle_external_request_error, views, matchers
    ):
        exception = views._context = ExternalRequestError(  # noqa: SLF001
            "External request failed", validation_errors={"foo": ["bar"]}
        )

        result = views.external_request()

        assert result == matchers.Redirect302To(pyramid_request.route_url("account"))
        assert pyramid_request.session.peek_flash("error") == [
            "Request to ORCID failed!"
        ]
        handle_external_request_error.assert_called_once_with(exception)

    def test_user_conflict_error(self, pyramid_request, views, matchers):
        result = views.user_conflict_error()

        assert result == matchers.Redirect302To(pyramid_request.route_url("account"))
        assert pyramid_request.session.peek_flash("error") == [
            "A different Hypothesis user is already connected to this ORCID account!"
        ]

    @pytest.fixture
    def views(self, pyramid_request):
        return SSORedirectViews(sentinel.context, pyramid_request)

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.session[STATE_SESSION_KEY_FMT.format(provider="orcid")] = (
            sentinel.state
        )
        pyramid_request.matched_route.name = "oidc.redirect.orcid"
        return pyramid_request

    @pytest.fixture
    def assert_state_removed_from_session(self, pyramid_request):
        """Assert that the `state` param was removed from the browser session.

        The redirect() view should always delete the single-use `state` from
        the browser session.
        """
        yield
        assert (
            STATE_SESSION_KEY_FMT.format(provider="orcid")
            not in pyramid_request.session
        )

    @pytest.fixture
    def assert_state_param_decoded_correctly(self, jwt_service, OAuth2RedirectSchema):
        yield
        jwt_service.decode_symmetric.assert_called_once_with(
            OAuth2RedirectSchema.validate.return_value["state"],
            audience=JWTAudiences.OIDC_REDIRECT_ORCID,
            payload_class=OIDCState,
        )

    @pytest.fixture
    def assert_success_message_was_flashed(self, pyramid_request):
        yield
        assert pyramid_request.session.peek_flash("success") == ["ORCID iD connected ✓"]

    @pytest.fixture
    def assert_no_success_message_was_flashed(self, pyramid_request):
        yield
        assert pyramid_request.session.peek_flash("success") == []

    @pytest.fixture(params=["connect", "login"])
    def with_both_connect_and_login_actions(self, request, set_action):
        """Run the test with both the "connect" and "login" actions.

        Tests using this fixture will be run twice: once with the "connect"
        action and once with the "login" action.
        """
        set_action(request.param)

    @pytest.fixture
    def with_connect_action(self, set_action):
        """Run the test with the "connect" action."""
        set_action("connect")

    @pytest.fixture
    def with_login_action(self, set_action):
        """Run the test with the "login" action."""
        set_action("login")

    @pytest.fixture
    def set_action(
        self, OAuth2RedirectSchema, pyramid_config, pyramid_request, user, jwt_service
    ):
        def set_action(action: str, authenticate_user=None):
            """Set the `action` string in the JWT `state` param to `action`."""
            OAuth2RedirectSchema.validate.return_value = {
                "code": sentinel.code,
                "state": sentinel.state,
            }
            jwt_service.decode_symmetric.return_value = OIDCState.make(action)

            if authenticate_user is None:
                if action == "connect":
                    # You have to be logged in to use the "connect" action, so
                    # most tests that use the "connect" action should have a
                    # logged-in user.
                    authenticate_user = True
                elif action == "login":
                    # You must be logged out to use the "login" action, so most
                    # tests that use the "login" action should *not* have a
                    # logged-in user.
                    authenticate_user = False

            if authenticate_user:
                # Set up a logged-in user.
                pyramid_config.testing_securitypolicy(userid=user.userid)
                pyramid_request.user = user

        return set_action

    @pytest.fixture
    def assert_no_account_connection_was_added(self, oidc_service):
        """Assert that no ORCID iD->Hypothesis account connection was added."""
        yield
        oidc_service.add_identity.assert_not_called()

    @pytest.fixture
    def assert_user_was_not_logged_in(self, login):
        """Assert that the browser session was not logged in."""
        yield
        login.assert_not_called()

    @pytest.fixture
    def orcid_id(self):
        return "test_orcid_id"

    @pytest.fixture
    def oidc_service(self, oidc_service, orcid_id):
        oidc_service.get_provider_unique_id.return_value = orcid_id
        return oidc_service

    @pytest.fixture
    def user_service(self, user_service, user):
        user_service.fetch_by_identity.return_value = user
        return user_service

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("activity.user_search", "/users/{username}")
        pyramid_config.add_route("account", "/account/settings")
        pyramid_config.add_route("signup.orcid", "/signup/orcid")

    @pytest.fixture(autouse=True)
    def handle_external_request_error(self, patch):
        return patch("h.views.oidc.handle_external_request_error")


class TestHandleExternalRequestError:
    def test_it(self, sentry_sdk, report_exception):
        exception = ExternalRequestError(
            message="External request failed",
            request=MagicMock(),
            response=MagicMock(),
        )

        handle_external_request_error(exception)

        assert sentry_sdk.set_context.call_args_list == [
            call(
                "request",
                {
                    "method": exception.method,
                    "url": exception.url,
                    "body": exception.request_body,
                },
            ),
            call(
                "response",
                {
                    "status_code": exception.status_code,
                    "reason": exception.reason,
                    "body": exception.response_body,
                },
            ),
        ]
        report_exception.assert_called_once_with(exception)

    def test_it_with_validation_errors(self, sentry_sdk):
        exception = ExternalRequestError(
            message="External request failed",
            request=MagicMock(),
            response=MagicMock(),
            validation_errors={"foo": ["bar"]},
        )

        handle_external_request_error(exception)

        assert sentry_sdk.set_context.call_args_list == [
            call(
                "request",
                {
                    "method": exception.method,
                    "url": exception.url,
                    "body": exception.request_body,
                },
            ),
            call(
                "response",
                {
                    "status_code": exception.status_code,
                    "reason": exception.reason,
                    "body": exception.response_body,
                },
            ),
            call("validation_errors", exception.validation_errors),
        ]


@pytest.fixture(autouse=True)
def sentry_sdk(patch):
    return patch("h.views.oidc.sentry_sdk")


@pytest.fixture(autouse=True)
def report_exception(patch):
    return patch("h.views.oidc.report_exception")


@pytest.fixture(autouse=True)
def OAuth2RedirectSchema(patch):
    return patch("h.views.oidc.OAuth2RedirectSchema")


@pytest.fixture(autouse=True)
def login(patch):
    return patch("h.views.oidc.login")


@pytest.fixture(autouse=True)
def secrets(patch):
    return patch("h.views.oidc.secrets")


@pytest.fixture(autouse=True)
def encode_idinfo_token(patch):
    return patch("h.views.oidc.encode_idinfo_token")
