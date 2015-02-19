# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from sqlalchemy import exc
from .. import models


class TestUser(object):
    def test_user_id_is_username(self):
        fred = models.User(username='fredbloggs',
                           email='fred@example.com',
                           password='123')

        assert fred.id == 'fredbloggs'

    def test_cannot_create_dot_variant_of_user(self, db_session):
        fred = models.User(username='fredbloggs',
                           email='fred@example.com',
                           password='123')
        fred2 = models.User(username='fred.bloggs',
                            email='fred@example.org',
                            password='456')

        db_session.add(fred)
        db_session.add(fred2)
        with pytest.raises(exc.IntegrityError):
            db_session.flush()

    def test_cannot_create_case_variant_of_user(self, db_session):
        bob = models.User(username='BobJones',
                          email='bob@example.com',
                          password='123')
        bob2 = models.User(username='bobjones',
                           email='bob@example.org',
                           password='456')

        db_session.add(bob)
        db_session.add(bob2)
        with pytest.raises(exc.IntegrityError):
            db_session.flush()
