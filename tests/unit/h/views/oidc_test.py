from unittest.mock import MagicMock, call, sentinel
from urllib.parse import urlencode, urlunparse

import jwt
import pytest
from pyramid.httpexceptions import HTTPForbidden

from h.models.user_identity import IdentityProvider
from h.schemas import ValidationError
from h.schemas.oauth import InvalidOAuth2StateParamError
from h.services.exceptions import ExternalRequestError
from h.views.oidc import (
    ORCID_STATE_SESSION_KEY,
    AccessDeniedError,
    ORCIDConnectAndLoginViews,
    ORCIDRedirectViews,
    UserConflictError,
    handle_external_request_error,
)


class TestORCIDAndLoginViews:
    @pytest.mark.parametrize(
        "route_name,expected_action",
        [
            ("oidc.connect.orcid", "connect"),
            ("oidc.login.orcid", "login"),
        ],
    )
    def test_connect_or_login(
        self, pyramid_request, secrets, signing_key, route_name, expected_action
    ):
        pyramid_request.matched_route.name = route_name

        result = ORCIDConnectAndLoginViews(pyramid_request).connect_or_login()

        expected_state = jwt.encode(
            {"action": expected_action, "rfp": secrets.token_hex.return_value},
            signing_key,
            algorithm="HS256",
        )

        assert pyramid_request.session[ORCID_STATE_SESSION_KEY] == expected_state
        assert result.location == urlunparse(
            (
                "https",
                IdentityProvider.ORCID,
                "oauth/authorize",
                "",
                urlencode(
                    {
                        "client_id": sentinel.client_id,
                        "response_type": "code",
                        "redirect_uri": pyramid_request.route_url(
                            "oidc.redirect.orcid"
                        ),
                        "state": expected_state,
                        "scope": "openid",
                    }
                ),
                "",
            )
        )

    def test_notfound(self, pyramid_request):
        pyramid_request.user = None

        result = ORCIDConnectAndLoginViews(pyramid_request).notfound()

        assert result == {}

    @pytest.fixture
    def pyramid_request(self, pyramid_request, factories, signing_key):
        pyramid_request.user = factories.User()
        pyramid_request.registry.settings.update(
            {
                "orcid_host": IdentityProvider.ORCID,
                "orcid_client_id": sentinel.client_id,
                "orcid_client_secret": sentinel.client_secret,
                "orcid_oidc_state_signing_key": signing_key,
            }
        )
        return pyramid_request

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("oidc.connect.orcid", "/oidc/connect/orcid")
        pyramid_config.add_route("oidc.redirect.orcid", "/oidc/redirect/orcid")

    @pytest.fixture(autouse=True)
    def secrets(self, secrets):
        # This just needs to be a string (not a mock) so that it's
        # JSON-serializable, the tests don't care about the actual value.
        secrets.token_hex.return_value = "test_rfp"
        return secrets


@pytest.mark.usefixtures("orcid_client_service", "user_service")
class TestORCIDRedirectViews:
    @pytest.mark.usefixtures(
        "with_both_connect_and_login_actions",
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
        "assert_no_success_message_was_flashed",
    )
    def test_redirect_when_theres_no_state_in_the_session(self, pyramid_request, views):
        del pyramid_request.session[ORCID_STATE_SESSION_KEY]

        with pytest.raises(InvalidOAuth2StateParamError):
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
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
        "assert_no_success_message_was_flashed",
    )
    def test_redirect_if_state_jwt_fails_to_decode(self, OAuth2RedirectSchema, views):
        OAuth2RedirectSchema.validate.return_value["state"] = "not_a_jwt"

        # This is deliberately not handled because it should never happen: the
        # code has already tested that the `state` query param that we received
        # from the authentication server matches the copy that we stashed in
        # the session, so the state should always decode without errors.
        with pytest.raises(jwt.exceptions.DecodeError):
            views.redirect()

    @pytest.mark.usefixtures(
        "assert_state_removed_from_session",
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
    def test_redirect_gets_the_users_orcid_id(self, views, orcid_client_service):
        views.redirect()

        orcid_client_service.get_orcid.assert_called_once_with(sentinel.code)

    @pytest.mark.usefixtures(
        "with_both_connect_and_login_actions",
        "assert_state_removed_from_session",
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
        "assert_no_success_message_was_flashed",
    )
    def test_redirect_when_getting_orcid_id_fails(self, views, orcid_client_service):
        class TestError(Exception):
            pass

        orcid_client_service.get_orcid.side_effect = TestError

        with pytest.raises(TestError):
            views.redirect()

    @pytest.mark.usefixtures("with_both_connect_and_login_actions")
    def test_redirect_fetches_the_hypothesis_uiser(self, views, user_service):
        views.redirect()

        user_service.fetch_by_identity.assert_called_once_with(
            IdentityProvider.ORCID, sentinel.orcid_id
        )

    @pytest.mark.usefixtures(
        "with_connect_action",
        "assert_state_removed_from_session",
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
        "assert_success_message_was_flashed",
        "assert_user_was_not_logged_in",
    )
    def test_redirect_when_action_connect_and_account_not_yet_connected(
        self, pyramid_request, orcid_client_service, user_service, user, views, matchers
    ):
        user_service.fetch_by_identity.return_value = None

        result = views.redirect()

        orcid_client_service.add_identity.assert_called_once_with(
            user, sentinel.orcid_id
        )
        assert result == matchers.Redirect302To(pyramid_request.route_url("account"))

    @pytest.mark.usefixtures(
        "with_connect_action",
        "assert_state_removed_from_session",
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
        "assert_no_account_connection_was_added",
        "assert_user_was_not_logged_in",
        "assert_no_success_message_was_flashed",
    )
    def test_redirect_when_action_login_and_no_connected_user_exists(
        self, views, user_service
    ):
        user_service.fetch_by_identity.return_value = None

        with pytest.raises(RuntimeError):
            views.redirect()

    @pytest.mark.usefixtures(
        "with_login_action",
        "assert_state_removed_from_session",
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

    def test_invalid(self, pyramid_request, views, matchers):
        result = views.invalid()

        assert result == matchers.Redirect302To(pyramid_request.route_url("account"))
        assert pyramid_request.session.peek_flash("error") == [
            "Received an invalid redirect from ORCID!"
        ]

    def test_invalid_token(self, pyramid_request, views, matchers):
        result = views.invalid_token()

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
        pyramid_request.exception = ExternalRequestError(
            "External request failed", validation_errors={"foo": ["bar"]}
        )
        result = views.external_request()

        assert result == matchers.Redirect302To(pyramid_request.route_url("account"))
        assert pyramid_request.session.peek_flash("error") == [
            "Request to ORCID failed!"
        ]
        handle_external_request_error.assert_called_once_with(pyramid_request.exception)

    def test_user_conflict_error(self, pyramid_request, views, matchers):
        result = views.user_conflict_error()

        assert result == matchers.Redirect302To(pyramid_request.route_url("account"))
        assert pyramid_request.session.peek_flash("error") == [
            "A different Hypothesis user is already connected to this ORCID iD!"
        ]

    @pytest.fixture
    def views(self, pyramid_request):
        return ORCIDRedirectViews(pyramid_request)

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def pyramid_request(self, pyramid_request, signing_key):
        pyramid_request.session[ORCID_STATE_SESSION_KEY] = sentinel.state
        pyramid_request.registry.settings.update(
            {"orcid_oidc_state_signing_key": signing_key}
        )
        return pyramid_request

    @pytest.fixture
    def assert_state_removed_from_session(self, pyramid_request):
        """Assert that the `state` param was removed from the browser session.

        The redirect() view should always delete the single-use `state` from
        the browser session.
        """
        yield
        assert ORCID_STATE_SESSION_KEY not in pyramid_request.session

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
        self, OAuth2RedirectSchema, signing_key, pyramid_config, pyramid_request, user
    ):
        def set_action(action: str, authenticate_user=None):
            """Set the `action` string in the JWT `state` param to `action`."""
            OAuth2RedirectSchema.validate.return_value = {
                "code": sentinel.code,
                "state": jwt.encode({"action": action}, signing_key, algorithm="HS256"),
            }

            if authenticate_user is None:
                if action == "connect":
                    # You have to be logged in to use the "connect" action, so
                    # most tests that use the "connect" action should have a
                    # logged-in user.
                    authenticate_user = True
                else:
                    # You must be logged out to use the "login" action, so most
                    # tests that use the "login" action should *not* have a
                    # logged-in user.
                    assert action == "login"
                    authenticate_user = False

            if authenticate_user:
                # Set up a logged-in user.
                pyramid_config.testing_securitypolicy(userid=user.userid)
                pyramid_request.user = user

        return set_action

    @pytest.fixture
    def assert_no_account_connection_was_added(self, orcid_client_service):
        """Assert that no ORCID iD->Hypothesis account connection was added."""
        yield
        orcid_client_service.add_identity.assert_not_called()

    @pytest.fixture
    def assert_user_was_not_logged_in(self, login):
        """Assert that the browser session was not logged in."""
        yield
        login.assert_not_called()

    @pytest.fixture
    def orcid_client_service(self, orcid_client_service):
        orcid_client_service.get_orcid.return_value = sentinel.orcid_id
        return orcid_client_service

    @pytest.fixture
    def user_service(self, user_service, user):
        user_service.fetch_by_identity.return_value = user
        return user_service

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("activity.user_search", "/users/{username}")
        pyramid_config.add_route("account", "/account/settings")

    @pytest.fixture(autouse=True)
    def handle_external_request_error(self, patch):
        return patch("h.views.oidc.handle_external_request_error")


class TestHandleExternalRequestError:
    def test_it(self, sentry_sdk):
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


@pytest.fixture
def signing_key():
    return "orcid_oidc_state_signing_key"


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
def secrets(patch):
    return patch("h.views.oidc.secrets")


@pytest.fixture(autouse=True)
def login(patch):
    return patch("h.views.oidc.login")
