# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest
from pyramid import exceptions
from pyramid import httpexceptions
from pyramid import testing

from h.views import client

annotator_token_fixtures = pytest.mark.usefixtures('generate_jwt', 'session')


@annotator_token_fixtures
def test_annotator_token_calls_check_csrf_token(session):
    request = testing.DummyRequest()

    client.annotator_token(request)

    session.check_csrf_token.assert_called_once_with(request,
                                                     token='assertion')


@annotator_token_fixtures
def test_annotator_token_raises_Unauthorized_if_check_csrf_token_raises(
        session):
    session.check_csrf_token.side_effect = exceptions.BadCSRFToken

    with pytest.raises(httpexceptions.HTTPUnauthorized):
        client.annotator_token(testing.DummyRequest())


@annotator_token_fixtures
def test_annotator_token_calls_generate_jwt(generate_jwt):
    request = testing.DummyRequest()

    client.annotator_token(request)

    generate_jwt.assert_called_once_with(request, 3600)


@annotator_token_fixtures
def test_annotator_token_returns_token(generate_jwt):
    request = testing.DummyRequest()

    result = client.annotator_token(request)

    assert result == generate_jwt.return_value


@pytest.fixture
def generate_jwt(request):
    patcher = mock.patch('h.views.client.generate_jwt', autospec=True)
    func = patcher.start()
    func.return_value = 'abc123'
    request.addfinalizer(patcher.stop)
    return func


@pytest.fixture
def session(request):
    patcher = mock.patch('h.views.client.session', autospec=True)
    module = patcher.start()
    request.addfinalizer(patcher.stop)
    return module
