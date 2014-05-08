# -*- coding: utf-8 -*-
"""Defines unit tests for h.models."""
from pyramid import authorization
from pyramid.testing import DummyRequest, testConfig

from h import models
from . import AppTestCase


class ModelTest(AppTestCase):
    """Model unit tests."""
    #pylint: disable=too-many-public-methods

    def test_password_encrypt(self):
        """make sure user passwords are stored encrypted
        """
        with testConfig(settings=self.settings) as config:
            authz = authorization.ACLAuthorizationPolicy()
            config.set_authorization_policy(authz)
            config.include('h.models')
            session = models.get_session(DummyRequest())
            user = models.User(username=u'test', password=u'test',
                               email=u'test@example.org')
            assert user.password != 'test'
            session.add(user)
            session.flush()
            assert user.password != 'test'
