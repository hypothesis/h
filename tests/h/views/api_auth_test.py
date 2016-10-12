# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h import models
from h.accounts.services import user_service_factory
from h.auth.services import oauth_service_factory, TOKEN_TTL
from h.exceptions import OAuthTokenError
from h.views import api_auth as views


@pytest.mark.usefixtures('user_service', 'oauth_service')
class TestAccessToken(object):
    def test_it_verifies_the_jwt_bearer(self, pyramid_request, oauth_service):
        pyramid_request.POST = {'assertion': 'the-assertion', 'grant_type': 'the-grant-type'}

        views.access_token(pyramid_request)

        oauth_service.verify_jwt_bearer.assert_called_once_with(
            assertion='the-assertion', grant_type='the-grant-type'
        )

    def test_it_creates_a_token(self, pyramid_request, oauth_service):
        user = mock.Mock()
        oauth_service.verify_jwt_bearer.return_value = user

        views.access_token(pyramid_request)

        oauth_service.create_token.assert_called_once_with(user)

    def test_it_returns_an_oauth_compliant_response(self, pyramid_request, oauth_service):
        token = models.Token()
        oauth_service.create_token.return_value = token

        assert views.access_token(pyramid_request) == {
            'access_token': token.value,
            'token_type': 'bearer',
            'expires_in': TOKEN_TTL.total_seconds(),
        }

    @pytest.fixture
    def oauth_service(self, pyramid_config, pyramid_request):
        svc = mock.Mock(spec_set=oauth_service_factory(None, pyramid_request))
        pyramid_config.register_service(svc, name='oauth')
        return svc

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
