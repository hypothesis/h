# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from sqlalchemy import inspect

from h.models import GroupScope


class TestGroupScope(object):
    def test_save_and_retrieve_origin(self, db_session, factories):
        origin = 'http://example.com'
        factories.GroupScope(origin=origin)

        group_scope = db_session.query(GroupScope).one()

        assert group_scope.origin == origin

    def test_subdomains_are_allowed_in_origin(self, db_session, factories):
        factories.GroupScope(origin='http://www.example.com')
        db_session.flush()

    def test_port_is_allowed_in_origin(self, db_session, factories):
        factories.GroupScope(origin='http://localhost:5000')
        db_session.flush()

    def test_there_is_no_validation_of_origin(self, db_session, factories):
        factories.GroupScope(origin='diplodocus : 123')
        db_session.flush()

    def test_you_can_get_a_groupscopes_group_by_the_group_property(
            self, factories):
        group = factories.OpenGroup()
        group_scope = factories.GroupScope(group=group)

        assert group_scope.group == group

    def test_you_can_get_a_groups_scopes_by_the_scopes_property(
            self, factories, matchers):
        group = factories.OpenGroup()
        scopes = [
            factories.GroupScope(group=group),
            factories.GroupScope(group=group),
            factories.GroupScope(group=group),
        ]

        assert group.scopes == matchers.unordered_list(scopes)

    def test_deleting_a_group_deletes_its_groupscopes(self, db_session,
                                                      factories):
        group = factories.OpenGroup()
        factories.GroupScope(group=group)
        factories.GroupScope(group=group)
        factories.GroupScope(group=group)

        db_session.delete(group)

        assert db_session.query(GroupScope).all() == []

    def test_removing_the_scopes_from_a_group_deletes_them(
            self, db_session, factories):
        group = factories.OpenGroup()
        factories.GroupScope(group=group)
        factories.GroupScope(group=group)
        factories.GroupScope(group=group)

        group.scopes = []

        assert db_session.query(GroupScope).all() == []

    def test_multiple_groupscopes_can_have_the_same_origin(
            self, db_session, factories):
        origin = 'http://example.com'
        group_1 = factories.OpenGroup()
        group_2 = factories.OpenGroup()
        group_3 = factories.OpenGroup()

        # Different groupscopes, belonging to different groups, can have the
        # same origin.
        factories.GroupScope(origin=origin, group=group_1)
        factories.GroupScope(origin=origin, group=group_2)
        factories.GroupScope(origin=origin, group=group_3)
        db_session.flush()

    def test_editing_a_groups_scopes_doesnt_affect_other_groups(
            self, factories):
        origin = 'http://example.com'
        group_1 = factories.OpenGroup()
        group_2 = factories.OpenGroup()
        group_3 = factories.OpenGroup()
        factories.GroupScope(origin=origin, group=group_1)
        factories.GroupScope(origin=origin, group=group_2)
        factories.GroupScope(origin=origin, group=group_3)

        group_1.scopes[0].origin = 'http://neworigin.com'

        assert group_1.scopes[0].origin == 'http://neworigin.com'
        assert group_2.scopes[0].origin == origin
        assert group_3.scopes[0].origin == origin

    def test_deleting_a_groups_scopes_doesnt_affect_other_groups(
            self, db_session, factories):
        origin = 'http://example.com'
        group_1 = factories.OpenGroup()
        group_2 = factories.OpenGroup()
        group_3 = factories.OpenGroup()
        db_session.add_all((
            factories.GroupScope(origin=origin, group=group_1),
            factories.GroupScope(origin=origin, group=group_2),
            factories.GroupScope(origin=origin, group=group_3),
        ))
        db_session.flush()

        db_session.delete(group_1.scopes[0])
        db_session.flush()

        assert inspect(group_1.scopes[0]).deleted
        assert not inspect(group_2.scopes[0]).deleted
        assert not inspect(group_3.scopes[0]).deleted

    def test_two_groups_cant_have_the_same_groupscope(self, factories):
        group_scope = factories.GroupScope()
        group_1 = group_scope.group

        group_2 = factories.OpenGroup(scopes=[group_scope])

        # Creating a new group with the same groupscope will have _moved_ the
        # scope to the new group. This is important because we never want a
        # single groupscope to belong to multiple groups, because we never want
        # editing one group's scopes to affect another group.
        assert group_2.scopes == [group_scope]
        assert group_1.scopes == []
