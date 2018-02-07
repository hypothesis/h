# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from sqlalchemy.exc import IntegrityError

from h.models import GroupScope


class TestGroupScope(object):

    def test_save_and_retrieve_hostname(self, db_session, factories):
        hostname = 'test_hostname'
        factories.GroupScope(hostname=hostname)
        group_scope = db_session.query(GroupScope).one()

        assert group_scope.hostname == 'test_hostname'

    def test_hostname_is_required(self, db_session, factories):
        with pytest.raises(IntegrityError):
            db_session.add(factories.GroupScope(hostname=None))

    def test_hostname_must_be_unique(self, db_session):
        hostname = 'test_hostname'
        db_session.add_all((GroupScope(hostname=hostname), GroupScope(hostname=hostname)))

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_a_single_group_can_have_many_scopes(self, db_session, factories, matchers):
        group = factories.Group()
        group_scopes = [
            factories.GroupScope(groups=[group]),
            factories.GroupScope(groups=[group]),
            factories.GroupScope(groups=[group]),
        ]
        db_session.add_all(group_scopes)
        db_session.flush()

        assert group.scopes == matchers.unordered_list(group_scopes)

    def test_a_single_scope_can_have_many_groups(self, db_session, factories, matchers):
        groups = [factories.Group(), factories.Group(), factories.Group()]
        group_scope = factories.GroupScope(groups=groups)
        db_session.add(group_scope)
        db_session.flush()

        assert group_scope.groups == matchers.unordered_list(groups)
