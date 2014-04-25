# -*- coding: utf-8 -*-
from pyramid import authorization
from pyramid.testing import DummyRequest, testConfig

from h import models
from . import AppTestCase


class ModelTest(AppTestCase):
    def test_password_encrypt(self):
        """make sure user passwords are stored encrypted
        """
        with testConfig(settings=self.settings) as config:
            authz = authorization.ACLAuthorizationPolicy()
            config.set_authorization_policy(authz)
            config.include('h.models')
            db = models.get_session(DummyRequest())
            u1 = models.User(username=u'test', password=u'test',
                             email=u'test@example.org')
            assert u1.password != 'test'
            db.add(u1)
            db.flush()
            assert u1.password != 'test'
