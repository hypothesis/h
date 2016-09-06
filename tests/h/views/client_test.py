# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from pyramid import exceptions
from pyramid import httpexceptions

from h.views import client

annotator_token_fixtures = pytest.mark.usefixtures('generate_jwt', 'session')


@annotator_token_fixtures
def test_annotator_token_calls_check_csrf_token(pyramid_request, session):
    client.annotator_token(pyramid_request)

    session.check_csrf_token.assert_called_once_with(pyramid_request)


@annotator_token_fixtures
def test_annotator_token_raises_Unauthorized_if_check_csrf_token_raises(
        pyramid_request,
        session):
    session.check_csrf_token.side_effect = exceptions.BadCSRFToken

    with pytest.raises(httpexceptions.HTTPUnauthorized):
        client.annotator_token(pyramid_request)


@annotator_token_fixtures
def test_annotator_token_calls_generate_jwt(generate_jwt, pyramid_request):
    client.annotator_token(pyramid_request)

    generate_jwt.assert_called_once_with(pyramid_request, 3600)


@annotator_token_fixtures
def test_annotator_token_returns_token(generate_jwt, pyramid_request):
    result = client.annotator_token(pyramid_request)

    assert result == generate_jwt.return_value


@pytest.fixture
def generate_jwt(patch):
    func = patch('h.views.client.generate_jwt')
    func.return_value = 'abc123'
    return func


@pytest.fixture
def session(patch):
    return patch('h.views.client.session')
