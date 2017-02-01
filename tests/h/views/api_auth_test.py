# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

import mock
import pytest

from h.services.oauth import oauth_service_factory
from h.services.user import user_service_factory
from h.exceptions import OAuthTokenError
from h.views import api_auth as views


@pytest.mark.usefixtures('user_service', 'oauth_service')
class TestAccessToken(object):
    def test_it_verifies_the_token(self, pyramid_request, oauth_service):
        pyramid_request.POST = {'assertion': 'the-assertion', 'grant_type': 'the-grant-type'}

        views.access_token(pyramid_request)

        oauth_service.verify_token_request.assert_called_once_with(
            pyramid_request.POST
        )

    def test_it_creates_a_token(self, pyramid_request, oauth_service):
        views.access_token(pyramid_request)

        oauth_service.create_token.assert_called_once_with(
            mock.sentinel.user, mock.sentinel.authclient)

    def test_it_returns_an_oauth_compliant_response(self, pyramid_request, token):
        response = views.access_token(pyramid_request)

        assert response['access_token'] == token.value
        assert response['token_type'] == 'bearer'

    def test_it_returns_expires_in_if_the_token_expires(self, factories, pyramid_request, oauth_service):
        token = factories.Token(
            expires=datetime.datetime.utcnow() + datetime.timedelta(hours=1))
        oauth_service.create_token.return_value = token

        assert 'expires_in' in views.access_token(pyramid_request)

    def test_it_does_not_return_expires_in_if_the_token_does_not_expire(self, pyramid_request):
        assert 'expires_in' not in views.access_token(pyramid_request)

    def test_it_returns_the_refresh_token_if_the_token_has_one(self, pyramid_request, token):
        token.refresh_token = 'test_refresh_token'

        assert views.access_token(pyramid_request)['refresh_token'] == token.refresh_token

    def test_it_does_not_returns_the_refresh_token_if_the_token_does_not_have_one(self, pyramid_request):
        assert 'refresh_token' not in views.access_token(pyramid_request)

    @pytest.fixture
    def oauth_service(self, pyramid_config, pyramid_request, token):
        svc = mock.Mock(spec_set=oauth_service_factory(None, pyramid_request))
        svc.verify_token_request.return_value = (mock.sentinel.user, mock.sentinel.authclient)
        svc.create_token.return_value = token
        pyramid_config.register_service(svc, name='oauth')
        return svc

    @pytest.fixture
    def token(self, factories):
        return factories.Token()

    @pytest.fixture
    def user_service(self, pyramid_config, pyramid_request):
        svc = mock.Mock(spec_set=user_service_factory(None, pyramid_request))
        pyramid_config.register_service(svc, name='user')
        return svc


class TestAPITokenError(object):
    def test_it_sets_the_response_status_code(self, pyramid_request):
        context = OAuthTokenError('the error message', 'error_type', status_code=403)
        views.api_token_error(context, pyramid_request)
        assert pyramid_request.response.status_code == 403

    def test_it_returns_the_error(self, pyramid_request):
        context = OAuthTokenError('', 'error_type')
        result = views.api_token_error(context, pyramid_request)
        assert result['error'] == 'error_type'

    def test_it_returns_error_description(self, pyramid_request):
        context = OAuthTokenError('error description', 'error_type')
        result = views.api_token_error(context, pyramid_request)
        assert result['error_description'] == 'error description'

    def test_it_skips_description_when_missing(self, pyramid_request):
        context = OAuthTokenError(None, 'invalid_request')
        result = views.api_token_error(context, pyramid_request)
        assert 'error_description' not in result

    def test_it_skips_description_when_empty(self, pyramid_request):
        context = OAuthTokenError('', 'invalid_request')
        result = views.api_token_error(context, pyramid_request)
        assert 'error_description' not in result
