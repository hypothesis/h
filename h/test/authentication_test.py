# -*- coding: utf-8 -*-
from collections import namedtuple

from mock import Mock, patch
from pyramid.interfaces import IAuthenticationPolicy
from pyramid.testing import DummyRequest, setUp

from h.authentication import OAuthPolicy
from h.models import Client
from h.oauth import IClientFactory


class MockClient(Mock):
    pass


def make_client(client_id):
    client = MockClient()
    client.client_id = client_id
    return client

mock_client_module = namedtuple('client_module', 'client_factory')


def test_oauth_policy():
    def verify_request():
        request.client = 'sloth'
        request.user = 'wizard'
        request.scopes = ['paris']

    request = DummyRequest()
    request.session = {}

    request.verify_request = verify_request
    policy = OAuthPolicy(prefix='app.')
    userid = policy.unauthenticated_userid(request)

    assert request.client == 'sloth'
    assert request.user == userid == 'wizard'
    assert request.scopes == ['paris']


def test_oauth_policy_session_user():
    request = DummyRequest()
    request.registry.web_client = None
    request.session = {'app.userid': 'mbatu'}
    policy = OAuthPolicy(prefix='app.')
    assert policy.unauthenticated_userid(request) == 'mbatu'


def test_includeme_sets_authentication_policy():
    config = setUp()
    config.set_authorization_policy(Mock())
    config.include('h.authentication')
    policy = config.registry.queryUtility(IAuthenticationPolicy)
    assert policy is not None


def test_includeme_sets_client_factory():
    config = setUp()
    config.set_authorization_policy(Mock())
    config.include('h.authentication')
    factory = config.registry.queryUtility(IClientFactory)
    assert factory is Client


@patch.dict('sys.modules', {'awesome_oauth': mock_client_module(make_client)})
def test_includeme_sets_client_factory_custom():
    settings = {'h.client_factory': 'awesome_oauth.client_factory'}
    config = setUp(settings=settings)
    config.set_authorization_policy(Mock())
    config.include('h.authentication')
    assert isinstance(config.registry.web_client, MockClient)
