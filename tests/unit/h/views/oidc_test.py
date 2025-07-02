from unittest.mock import MagicMock, Mock, call, sentinel
from urllib.parse import urlencode, urlunparse

import pytest
from pyramid.httpexceptions import HTTPFound

import h.views.oidc as views
from h.models.user_identity import IdentityProvider
from h.schemas import ValidationError
from h.services.exceptions import ExternalRequestError
from h.services.jwt import TokenValidationError


class TestORCIDAuthorizeViews:
    def test_authorize(self, pyramid_request):
        result = views.ORCIDAuthorizeViews(pyramid_request).authorize()

        assert isinstance(result, HTTPFound)
        params = {
            "client_id": sentinel.client_id,
            "response_type": "code",
            "redirect_uri": pyramid_request.route_url("oidc.redirect.orcid"),
            "state": sentinel.state_param,
            "scope": "openid",
        }
        assert result.location == urlunparse(
            (
                "https",
                IdentityProvider.ORCID,
                "oauth/authorize",
                "",
                urlencode(params),
                "",
            )
        )

    def test_notfound(self, pyramid_request):
        pyramid_request.user = None

        result = views.ORCIDAuthorizeViews(pyramid_request).notfound()

        assert result == {}

    @pytest.fixture
    def pyramid_request(self, pyramid_request, factories):
        pyramid_request.user = factories.User()
        pyramid_request.registry.settings.update(
            {
                "orcid_host": IdentityProvider.ORCID,
                "orcid_client_id": sentinel.client_id,
                "orcid_client_secret": sentinel.client_secret,
            }
        )
        return pyramid_request

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("oidc.authorize.orcid", "/oidc/authorize/orcid")
        pyramid_config.add_route("oidc.redirect.orcid", "/oidc/redirect/orcid")


@pytest.mark.usefixtures("orcid_client_service", "user_service")
class TestORCIDRedirectViews:
    def test_it(self, pyramid_request, orcid_client_service, user_service, user):
        orcid = orcid_client_service.get_orcid.return_value
        user_service.fetch_by_identity.return_value = None

        result = views.ORCIDRedirectViews(pyramid_request).redirect()

        assert isinstance(result, HTTPFound)
        assert result.location == pyramid_request.route_url("account")
        orcid_client_service.get_orcid.assert_called_once_with(sentinel.code)
        orcid_client_service.add_identity.assert_called_once_with(user, orcid)
        pyramid_request.session.flash.assert_called_once_with(
            "ORCID iD connected ✓", "success"
        )

    def test_it_raises_validation_error(self, pyramid_request, OAuth2RedirectSchema):
        OAuth2RedirectSchema.return_value.validate.side_effect = ValidationError()
        pyramid_request.params = {}

        with pytest.raises(ValidationError):
            views.ORCIDRedirectViews(pyramid_request).redirect()

    def test_it_raises_access_denied_error(self, pyramid_request, OAuth2RedirectSchema):
        OAuth2RedirectSchema.return_value.validate.side_effect = ValidationError()
        pyramid_request.params = {"error": "access_denied"}

        with pytest.raises(views.AccessDeniedError):
            views.ORCIDRedirectViews(pyramid_request).redirect()

    def test_it_raises_token_validation_error(
        self, pyramid_request, orcid_client_service
    ):
        orcid_client_service.get_orcid.side_effect = TokenValidationError(
            "Invalid token"
        )

        with pytest.raises(TokenValidationError):
            views.ORCIDRedirectViews(pyramid_request).redirect()

    def test_it_raises_external_request_error(
        self, pyramid_request, orcid_client_service
    ):
        orcid_client_service.get_orcid.side_effect = ExternalRequestError(
            "External request failed"
        )

        with pytest.raises(ExternalRequestError):
            views.ORCIDRedirectViews(pyramid_request).redirect()

    def test_it_raises_user_conflict_error(
        self, pyramid_request, user_service, factories
    ):
        other_user = factories.User()
        user_service.fetch_by_identity.return_value = other_user

        with pytest.raises(views.UserConflictError):
            views.ORCIDRedirectViews(pyramid_request).redirect()

    def test_it_is_already_connected(
        self, pyramid_request, orcid_client_service, user_service, user
    ):
        user_service.fetch_by_identity.return_value = user

        result = views.ORCIDRedirectViews(pyramid_request).redirect()

        assert isinstance(result, HTTPFound)
        assert result.location == pyramid_request.route_url("account")
        orcid_client_service.get_orcid.assert_called_once_with(sentinel.code)
        orcid_client_service.add_identity.assert_not_called()
        pyramid_request.session.flash.assert_called_once_with(
            "ORCID iD connected ✓", "success"
        )

    def test_notfound(self, pyramid_request):
        result = views.ORCIDRedirectViews(pyramid_request).notfound()

        assert result == {}

    def test_invalid(self, pyramid_request):
        result = views.ORCIDRedirectViews(pyramid_request).invalid()

        assert isinstance(result, HTTPFound)
        assert result.location == pyramid_request.route_url("account")
        pyramid_request.session.flash.assert_called_once_with(
            "Received an invalid redirect from ORCID!", "error"
        )

    def test_invalid_token(self, pyramid_request):
        result = views.ORCIDRedirectViews(pyramid_request).invalid_token()

        assert isinstance(result, HTTPFound)
        assert result.location == pyramid_request.route_url("account")
        pyramid_request.session.flash.assert_called_once_with(
            "Received an invalid token from ORCID!", "error"
        )

    def test_denied(self, pyramid_request):
        result = views.ORCIDRedirectViews(pyramid_request).denied()

        assert isinstance(result, HTTPFound)
        assert result.location == pyramid_request.route_url("account")
        pyramid_request.session.flash.assert_called_once_with(
            "The user clicked the deny button!", "error"
        )

    def test_external_request(self, pyramid_request, handle_external_request_error):
        pyramid_request.exception = ExternalRequestError(
            "External request failed", validation_errors={"foo": ["bar"]}
        )
        result = views.ORCIDRedirectViews(pyramid_request).external_request()

        assert isinstance(result, HTTPFound)
        assert result.location == pyramid_request.route_url("account")
        pyramid_request.session.flash.assert_called_once_with(
            "Request to ORCID failed!", "error"
        )
        handle_external_request_error.assert_called_once_with(pyramid_request.exception)

    def test_user_conflict_error(self, pyramid_request):
        result = views.ORCIDRedirectViews(pyramid_request).user_conflict_error()

        assert isinstance(result, HTTPFound)
        pyramid_request.session.flash.assert_called_once_with(
            "A different Hypothesis user is already connected to this ORCID iD!",
            "error",
        )
        assert result.location == pyramid_request.route_url("account")

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def pyramid_request(self, pyramid_request, user):
        pyramid_request.user = user
        pyramid_request.session.flash = Mock()
        return pyramid_request

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("account", "/account/settings")
        pyramid_config.add_route("index", "/")

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

        views.handle_external_request_error(exception)

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

        views.handle_external_request_error(exception)

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
    OAuth2RedirectSchema = patch("h.views.oidc.OAuth2RedirectSchema")
    OAuth2RedirectSchema.return_value.validate.return_value = {"code": sentinel.code}
    OAuth2RedirectSchema.return_value.state_param.return_value = sentinel.state_param
    return OAuth2RedirectSchema
