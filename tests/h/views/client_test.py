# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.views import client


def test_annotator_token_calls_generate_jwt(generate_jwt, pyramid_request):
    client.annotator_token(pyramid_request)

    generate_jwt.assert_called_once_with(pyramid_request, 3600)


def test_annotator_token_returns_token(generate_jwt, pyramid_request):
    result = client.annotator_token(pyramid_request)

    assert result == generate_jwt.return_value


@pytest.fixture
def generate_jwt(patch):
    func = patch('h.views.client.generate_jwt')
    func.return_value = 'abc123'
    return func
