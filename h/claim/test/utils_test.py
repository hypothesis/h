# -*- coding: utf-8 -*-
import mock
import pytest

from pyramid import testing

from ..util import generate_claim_url


def test_generate_claim_url():
    serializer = mock.Mock()
    serializer.dumps.return_value = 'faketoken'

    request = testing.DummyRequest()
    request.registry.claim_serializer = serializer

    url = generate_claim_url(request, 'acct:bob@example.com')

    assert url == 'http://example.com/dummy/claim/faketoken'
    serializer.dumps.assert_called_with({'userid': 'acct:bob@example.com'})


@pytest.fixture(autouse=True)
def routes(config):
    """Add routes used by claim package"""
    config.add_route('claim_account', '/dummy/claim/{token}')
