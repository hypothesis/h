# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
import json

import mock
import pytest

from oauthlib.oauth2 import InvalidRequestFatalError
from oauthlib.common import Request as OAuthRequest
from pyramid import httpexceptions

from h._compat import urlparse
from h.views.api.exceptions import OAuthTokenError
from h.models.auth_client import ResponseType
from h.services.auth_token import auth_token_service_factory
from h.services.oauth_provider import OAuthProviderService
from h.services.oauth_validator import DEFAULT_SCOPES
from h.services.user import user_service_factory
from h.util.datetime import utc_iso8601
from h.views.api import auth as views
from h.views.api.exceptions import OAuthAuthorizeError


@pytest.mark.usefixtures("routes", "oauth_provider", "user_svc")
class TestOAuthAuthorizeController(object):
    @pytest.mark.usefixtures("authenticated_user")
    @pytest.mark.parametrize("view_name", ["get", "get_web_message"])
    def test_get_validates_request(self, controller, pyramid_request, view_name):
        view = getattr(controller, view_name)
        view()

        controller.oauth.validate_authorization_request.assert_called_once_with(
            pyramid_request.url
        )

    @pytest.mark.parametrize("view_name", ["get", "get_web_message"])
    def test_get_raises_for_invalid_request(self, controller, view_name):
        controller.oauth.validate_authorization_request.side_effect = InvalidRequestFatalError(
            "boom!"
        )

        with pytest.raises(OAuthAuthorizeError) as exc:
            view = getattr(controller, view_name)
            view()

        assert exc.value.detail == "boom!"

    @pytest.mark.parametrize("view_name", ["get", "get_web_message"])
    def test_get_redirects_to_login_when_not_authenticated(
        self, controller, pyramid_request, view_name
    ):
        with pytest.raises(httpexceptions.HTTPFound) as exc:
            view = getattr(controller, view_name)
            view()

        parsed_url = urlparse.urlparse(exc.value.location)
        assert parsed_url.path == "/login"
        assert urlparse.parse_qs(parsed_url.query) == {
            "next": [pyramid_request.url],
            "for_oauth": ["True"],
        }

    @pytest.mark.parametrize(
        "response_mode,view_name", [(None, "get"), ("web_message", "get_web_message")]
    )
    def test_get_returns_expected_context(
        self,
        controller,
        auth_client,
        authenticated_user,
        oauth_request,
        response_mode,
        view_name,
    ):
        oauth_request.response_mode = response_mode

        view = getattr(controller, view_name)
        assert view() == {
            "client_id": auth_client.id,
            "client_name": auth_client.name,
            "response_mode": response_mode,
            "response_type": auth_client.response_type.value,
            "state": "foobar",
            "username": authenticated_user.username,
        }

    @pytest.mark.parametrize("view_name", ["get", "get_web_message"])
    def test_get_creates_authorization_response_for_trusted_clients(
        self, controller, auth_client, authenticated_user, pyramid_request, view_name
    ):
        auth_client.trusted = True

        view = getattr(controller, view_name)
        view()

        controller.oauth.create_authorization_response.assert_called_once_with(
            pyramid_request.url,
            credentials={"user": authenticated_user},
            scopes=DEFAULT_SCOPES,
        )

    def test_get_returns_redirect_immediately_for_trusted_clients(
        self, controller, auth_client, authenticated_user, pyramid_request
    ):
        auth_client.trusted = True

        response = controller.get()
        expected = "{}?code=abcdef123456&state=foobar".format(auth_client.redirect_uri)

        assert response.location == expected

    @pytest.mark.usefixtures("authenticated_user")
    def test_get_web_message_renders_template_for_trusted_clients(
        self, controller, auth_client
    ):
        auth_client.trusted = True

        assert controller.request.override_renderer is None
        controller.get_web_message()
        assert (
            controller.request.override_renderer
            == "h:templates/oauth/authorize_web_message.html.jinja2"
        )

    @pytest.mark.usefixtures("authenticated_user")
    def test_get_web_message_returns_context_for_trusted_clients(
        self, controller, auth_client
    ):
        auth_client.trusted = True

        response = controller.get_web_message()

        assert response == {
            "code": "abcdef123456",
            "origin": "http://client.com",
            "state": "foobar",
        }

    @pytest.mark.usefixtures("authenticated_user")
    def test_get_web_message_allows_empty_state_in_context_for_trusted_clients(
        self, controller, auth_client, oauth_provider
    ):
        auth_client.trusted = True

        headers = {"Location": "{}?code=abcdef123456".format(auth_client.redirect_uri)}
        oauth_provider.create_authorization_response.return_value = (headers, None, 302)

        response = controller.get_web_message()
        assert response["state"] is None

    @pytest.mark.parametrize("view_name", ["post", "post_web_message"])
    def test_post_creates_authorization_response(
        self, controller, pyramid_request, authenticated_user, view_name
    ):
        pyramid_request.url = (
            "http://example.com/auth?client_id=the-client-id"
            + "&response_type=code"
            + "&state=foobar"
            + "&scope=exploit"
        )

        view = getattr(controller, view_name)
        view()

        controller.oauth.create_authorization_response.assert_called_once_with(
            pyramid_request.url,
            credentials={"user": authenticated_user},
            scopes=DEFAULT_SCOPES,
        )

    @pytest.mark.usefixtures("authenticated_user")
    @pytest.mark.parametrize("view_name", ["post", "post_web_message"])
    def test_post_raises_for_invalid_request(self, controller, view_name):
        controller.oauth.create_authorization_response.side_effect = InvalidRequestFatalError(
            "boom!"
        )

        with pytest.raises(InvalidRequestFatalError) as exc:
            view = getattr(controller, view_name)
            view()

        assert exc.value.description == "boom!"

    def test_post_redirects_to_client(self, controller, auth_client):
        response = controller.post()
        expected = "{}?code=abcdef123456&state=foobar".format(auth_client.redirect_uri)

        assert response.location == expected

    def test_post_web_message_returns_expected_context(self, controller, auth_client):
        response = controller.post_web_message()

        assert response == {
            "code": "abcdef123456",
            "origin": "http://client.com",
            "state": "foobar",
        }

    def test_post_web_message_allows_empty_state_in_context(
        self, controller, auth_client, oauth_provider
    ):
        auth_client.trusted = True

        headers = {"Location": "{}?code=abcdef123456".format(auth_client.redirect_uri)}
        oauth_provider.create_authorization_response.return_value = (headers, None, 302)

        response = controller.post_web_message()
        assert response["state"] is None

    @pytest.fixture
    def controller(self, pyramid_request):
        pyramid_request.override_renderer = None
        return views.OAuthAuthorizeController(None, pyramid_request)

    @pytest.fixture
    def oauth_request(self):
        return OAuthRequest("/")

    @pytest.fixture
    def oauth_provider(self, pyramid_config, auth_client, oauth_request):
        svc = mock.create_autospec(OAuthProviderService, instance=True)

        scopes = ["annotation:read", "annotation:write"]
        credentials = {
            "client_id": auth_client.id,
            "state": "foobar",
            "request": oauth_request,
        }
        svc.validate_authorization_request.return_value = (scopes, credentials)

        headers = {
            "Location": "{}?code=abcdef123456&state=foobar".format(
                auth_client.redirect_uri
            )
        }
        body = None
        status = 302
        svc.create_authorization_response.return_value = (headers, body, status)

        pyramid_config.register_service(svc, name="oauth_provider")

        return svc

    @pytest.fixture
    def auth_client(self, factories):
        return factories.AuthClient(
            name="Test Client",
            redirect_uri="http://client.com/auth/callback",
            response_type=ResponseType.code,
        )

    @pytest.fixture
    def user_svc(self, pyramid_config, pyramid_request):
        svc = mock.Mock(spec_set=user_service_factory(None, pyramid_request))
        pyramid_config.register_service(svc, name="user")
        return svc

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.url = "http://example.com/auth?client_id=the-client-id&response_type=code&state=foobar"
        return pyramid_request

    @pytest.fixture
    def authenticated_user(self, factories, pyramid_config, user_svc):
        user = factories.User.build()
        pyramid_config.testing_securitypolicy(user.userid)

        def fake_fetch(userid):
            if userid == user.userid:
                return user

        user_svc.fetch.side_effect = fake_fetch

        return user

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route("login", "/login")


@pytest.mark.usefixtures("oauth_provider")
class TestOAuthAccessTokenController(object):
    def test_it_creates_token_response(
        self, pyramid_request, controller, oauth_provider
    ):
        controller.post()
        oauth_provider.create_token_response.assert_called_once_with(
            pyramid_request.url,
            pyramid_request.method,
            pyramid_request.POST,
            pyramid_request.headers,
        )

    def test_it_returns_correct_response_on_success(self, controller, oauth_provider):
        body = json.dumps({"access_token": "the-access-token"})
        oauth_provider.create_token_response.return_value = ({}, body, 200)

        assert controller.post() == {"access_token": "the-access-token"}

    def test_it_raises_when_error(self, controller, oauth_provider):
        body = json.dumps({"error": "invalid_request"})
        oauth_provider.create_token_response.return_value = ({}, body, 400)

        with pytest.raises(httpexceptions.HTTPBadRequest) as exc:
            controller.post()

        assert exc.value.body == body.encode()

    @pytest.fixture
    def controller(self, pyramid_request):
        pyramid_request.method = "POST"
        pyramid_request.POST["grant_type"] = "authorization_code"
        pyramid_request.POST["code"] = "the-authz-code"
        pyramid_request.headers = {"X-Test-ID": "1234"}
        return views.OAuthAccessTokenController(pyramid_request)

    @pytest.fixture
    def oauth_provider(self, pyramid_config):
        svc = mock.Mock(spec_set=["create_token_response"])
        svc.create_token_response.return_value = ({}, "{}", 200)
        pyramid_config.register_service(svc, name="oauth_provider")
        return svc


@pytest.mark.usefixtures("oauth_provider")
class TestOAuthRevocationController(object):
    def test_it_creates_revocation_response(
        self, pyramid_request, controller, oauth_provider
    ):
        controller.post()
        oauth_provider.create_revocation_response.assert_called_once_with(
            pyramid_request.url,
            pyramid_request.method,
            pyramid_request.POST,
            pyramid_request.headers,
        )

    def test_it_returns_empty_response_on_success(self, controller):
        response = controller.post()
        assert response == {}

    def test_it_raises_when_error(self, controller, oauth_provider):
        body = json.dumps({"error": "invalid_request"})
        oauth_provider.create_revocation_response.return_value = ({}, body, 400)

        with pytest.raises(httpexceptions.HTTPBadRequest) as exc:
            controller.post()

        assert exc.value.body == body.encode()

    @pytest.fixture
    def controller(self, pyramid_request):
        pyramid_request.method = "POST"
        pyramid_request.POST["token"] = "the-token"
        pyramid_request.headers = {"X-Test-ID": "1234"}
        return views.OAuthRevocationController(pyramid_request)

    @pytest.fixture
    def oauth_provider(self, pyramid_config):
        svc = mock.Mock(spec_set=["create_revocation_response"])
        svc.create_revocation_response.return_value = ({}, "{}", 200)
        pyramid_config.register_service(svc, name="oauth_provider")
        return svc


class TestDebugToken(object):
    def test_it_raises_error_when_token_is_missing(self, pyramid_request):
        pyramid_request.auth_token = None

        with pytest.raises(OAuthTokenError) as exc:
            views.debug_token(pyramid_request)

        assert exc.value.type == "missing_token"
        assert "Bearer token is missing" in str(exc.value)

    def test_it_raises_error_when_token_is_empty(self, pyramid_request):
        pyramid_request.auth_token = ""

        with pytest.raises(OAuthTokenError) as exc:
            views.debug_token(pyramid_request)

        assert exc.value.type == "missing_token"
        assert "Bearer token is missing" in str(exc.value)

    def test_it_validates_token(self, pyramid_request, token_service):
        pyramid_request.auth_token = "the-access-token"

        views.debug_token(pyramid_request)

        token_service.validate.assert_called_once_with("the-access-token")

    def test_it_raises_error_when_token_is_invalid(
        self, pyramid_request, token_service
    ):
        pyramid_request.auth_token = "the-token"
        token_service.validate.return_value = None

        with pytest.raises(OAuthTokenError) as exc:
            views.debug_token(pyramid_request)

        assert exc.value.type == "missing_token"
        assert "Bearer token does not exist or is expired" in str(exc.value)

    def test_returns_debug_data_for_oauth_token(
        self, pyramid_request, token_service, oauth_token
    ):
        pyramid_request.auth_token = oauth_token.value
        token_service.fetch.return_value = oauth_token

        result = views.debug_token(pyramid_request)

        assert result == {
            "userid": oauth_token.userid,
            "client": {
                "id": oauth_token.authclient.id,
                "name": oauth_token.authclient.name,
            },
            "issued_at": utc_iso8601(oauth_token.created),
            "expires_at": utc_iso8601(oauth_token.expires),
            "expired": oauth_token.expired,
        }

    def test_returns_debug_data_for_developer_token(
        self, pyramid_request, token_service, developer_token
    ):
        pyramid_request.auth_token = developer_token.value
        token_service.fetch.return_value = developer_token

        result = views.debug_token(pyramid_request)

        assert result == {
            "userid": developer_token.userid,
            "issued_at": utc_iso8601(developer_token.created),
            "expires_at": None,
            "expired": False,
        }

    @pytest.fixture
    def token_service(self, pyramid_config, pyramid_request):
        svc = mock.Mock(spec_set=auth_token_service_factory(None, pyramid_request))
        pyramid_config.register_service(svc, name="auth_token")
        return svc

    @pytest.fixture
    def oauth_token(self, factories):
        authclient = factories.AuthClient(name="Example Client")
        expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        return factories.DeveloperToken(authclient=authclient, expires=expires)

    @pytest.fixture
    def developer_token(self, factories):
        return factories.DeveloperToken()


class TestAPITokenError(object):
    def test_it_sets_the_response_status_code(self, pyramid_request):
        context = OAuthTokenError("the error message", "error_type")
        views.api_token_error(context, pyramid_request)
        assert pyramid_request.response.status_code == 401

    def test_it_returns_the_error(self, pyramid_request):
        context = OAuthTokenError("", "error_type")
        result = views.api_token_error(context, pyramid_request)
        assert result["error"] == "error_type"

    def test_it_returns_error_description(self, pyramid_request):
        context = OAuthTokenError("error description", "error_type")
        result = views.api_token_error(context, pyramid_request)
        assert result["error_description"] == "error description"

    def test_it_skips_description_when_missing(self, pyramid_request):
        context = OAuthTokenError(None, "invalid_request")
        result = views.api_token_error(context, pyramid_request)
        assert "error_description" not in result

    def test_it_skips_description_when_empty(self, pyramid_request):
        context = OAuthTokenError("", "invalid_request")
        result = views.api_token_error(context, pyramid_request)
        assert "error_description" not in result
