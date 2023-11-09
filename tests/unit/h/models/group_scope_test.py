import pytest
from h_matchers import Any
from sqlalchemy import inspect

from h.models import GroupScope


class TestGroupScope:
    def test_save_and_retrieve_scope(self, db_session, factories):
        scope = "http://example.com"
        factories.GroupScope(scope=scope)

        group_scope = db_session.query(GroupScope).one()

        assert group_scope.scope == scope

    def test_subdomains_are_allowed_in_scope(self, db_session, factories):
        factories.GroupScope(scope="http://www.example.com")
        db_session.flush()

    def test_port_is_allowed_in_scope(self, db_session, factories):
        factories.GroupScope(scope="http://localhost:5000")
        db_session.flush()

    def test_it_raises_if_scope_has_no_origin(self, factories):
        with pytest.raises(ValueError, match="Invalid URL"):
            factories.GroupScope(scope="diplodocus : 123")

    def test_setting_scope_property_sets_origin(self, factories):
        group_scope = factories.GroupScope(scope="http://www.foo.com/bar/baz")

        assert group_scope.origin == "http://www.foo.com"
        assert group_scope.scope == "http://www.foo.com/bar/baz"

    def test_it_raises_if_origin_set_directly(self, factories):
        with pytest.raises(AttributeError):
            factories.GroupScope(origin="http://www.foo.com")

    def test_it_raises_if_path_accessed(self, factories):
        scope = factories.GroupScope()
        with pytest.raises(AttributeError):
            _ = scope.path

    def test_you_can_get_a_groupscopes_group_by_the_group_property(self, factories):
        group = factories.OpenGroup()
        group_scope = factories.GroupScope(group=group)

        assert group_scope.group == group

    def test_you_can_get_a_groups_scopes_by_the_scopes_property(self, factories):
        group = factories.OpenGroup()
        scopes = [
            factories.GroupScope(group=group),
            factories.GroupScope(group=group),
            factories.GroupScope(group=group),
        ]

        assert group.scopes == Any.list.containing(scopes).only()

    def test_deleting_a_group_deletes_its_groupscopes(self, db_session, factories):
        group = factories.OpenGroup()
        factories.GroupScope(group=group)
        factories.GroupScope(group=group)
        factories.GroupScope(group=group)

        db_session.delete(group)

        assert db_session.query(GroupScope).all() == []

    def test_removing_the_scopes_from_a_group_deletes_them(self, db_session, factories):
        group = factories.OpenGroup()
        factories.GroupScope(group=group)
        factories.GroupScope(group=group)
        factories.GroupScope(group=group)

        group.scopes = []

        assert db_session.query(GroupScope).all() == []

    def test_multiple_groupscopes_can_have_the_same_scope(self, db_session, factories):
        scope = "http://example.com"
        group_1 = factories.OpenGroup()
        group_2 = factories.OpenGroup()
        group_3 = factories.OpenGroup()

        # Different groupscopes, belonging to different groups, can have the
        # same origin.
        factories.GroupScope(scope=scope, group=group_1)
        factories.GroupScope(scope=scope, group=group_2)
        factories.GroupScope(scope=scope, group=group_3)
        db_session.flush()

    def test_editing_a_groups_scopes_doesnt_affect_other_groups(self, factories):
        scope = "http://example.com"
        group_1 = factories.OpenGroup()
        group_2 = factories.OpenGroup()
        group_3 = factories.OpenGroup()
        factories.GroupScope(scope=scope, group=group_1)
        factories.GroupScope(scope=scope, group=group_2)
        factories.GroupScope(scope=scope, group=group_3)

        group_1.scopes[0].scope = "http://neworigin.com"

        assert group_1.scopes[0].scope == "http://neworigin.com"
        assert group_2.scopes[0].scope == scope
        assert group_3.scopes[0].scope == scope

    def test_deleting_a_groups_scopes_doesnt_affect_other_groups(
        self, db_session, factories
    ):
        scope = "http://example.com"
        group_1 = factories.OpenGroup()
        group_2 = factories.OpenGroup()
        group_3 = factories.OpenGroup()
        db_session.add_all(
            (
                factories.GroupScope(scope=scope, group=group_1),
                factories.GroupScope(scope=scope, group=group_2),
                factories.GroupScope(scope=scope, group=group_3),
            )
        )
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
