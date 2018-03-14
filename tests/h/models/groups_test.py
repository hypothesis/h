# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy

from h import models
from h.models.group import JoinableBy, ReadableBy, WriteableBy


def test_init_sets_given_attributes():
    group = models.Group(name='My group', authority='example.com')

    assert group.name == 'My group'
    assert group.authority == 'example.com'


def test_with_short_name():
    """Should raise ValueError if name shorter than 4 characters."""
    with pytest.raises(ValueError):
        models.Group(name="abc")


def test_with_long_name():
    """Should raise ValueError if name longer than 25 characters."""
    with pytest.raises(ValueError):
        models.Group(name="abcdefghijklmnopqrstuvwxyz")


def test_slug(db_session, factories):
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, authority="foobar.com", creator=user)
    db_session.add(group)
    db_session.flush()

    assert group.slug == "my-hypothesis-group"


def test_type_returns_open_for_open_groups(factories):
    assert factories.OpenGroup().type == 'open'


def test_type_returns_private_for_private_groups(factories):
    assert factories.Group().type == 'private'


def test_type_returns_restricted_for_restricted_groups(factories):
    assert factories.RestrictedGroup().type == 'restricted'


def test_type_raises_for_unknown_type_of_group(factories):
    group = factories.Group()
    # Set the group's access flags to an invalid / unused combination.
    group.joinable_by = None
    group.readable_by = ReadableBy.members
    group.writeable_by = WriteableBy.authority

    expected_err = "^This group doesn't seem to match any known type"
    with pytest.raises(ValueError, match=expected_err):
        group.type


def test_you_cannot_set_type(factories):
    group = factories.Group()

    with pytest.raises(AttributeError, match="can't set attribute"):
        group.type = 'open'


def test_repr(db_session, factories):
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, authority='foobar.com', creator=user)
    db_session.add(group)
    db_session.flush()

    assert repr(group) == "<Group: my-hypothesis-group>"


def test_gets_logo_if_logo_is_known(db_session, factories):
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, authority='biopub.hypothes.is', creator=user)
    db_session.add(group)
    db_session.flush()

    assert group.logo == "biopub-logo"


def test_returns_none_if_logo_is_unknown(db_session, factories):
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(name=name, authority='foobar.com', creator=user)
    db_session.add(group)
    db_session.flush()

    assert group.logo is None


def test_created_by(db_session, factories):
    name_1 = "My first group"
    name_2 = "My second group"
    user = factories.User()

    group_1 = models.Group(name=name_1, authority='foobar.com', creator=user)
    group_2 = models.Group(name=name_2, authority='foobar.com', creator=user)

    db_session.add_all([group_1, group_2])
    db_session.flush()

    assert models.Group.created_by(db_session, user).all() == [group_1, group_2]


def test_public_group():
    group = models.Group(readable_by=ReadableBy.world)

    assert group.is_public


def test_non_public_group():
    group = models.Group(readable_by=ReadableBy.members)

    assert not group.is_public


class TestGroupACL(object):
    def test_authority_joinable(self, group, authz_policy):
        group.joinable_by = JoinableBy.authority

        assert authz_policy.permits(group, ['userid', 'authority:example.com'], 'join')

    def test_not_joinable(self, group, authz_policy):
        group.joinable_by = None
        assert not authz_policy.permits(group, ['userid', 'authority:example.com'], 'join')

    def test_world_readable(self, group, authz_policy):
        group.readable_by = ReadableBy.world
        assert authz_policy.permits(group, [security.Everyone], 'read')

    def test_members_readable(self, group, authz_policy):
        group.readable_by = ReadableBy.members
        assert authz_policy.permits(group, ['group:test-group'], 'read')

    def test_not_readable(self, group, authz_policy):
        group.readable_by = None
        assert not authz_policy.permits(group, [security.Everyone, 'group:test-group'], 'read')

    def test_authority_writeable(self, group, authz_policy):
        group.writeable_by = WriteableBy.authority
        assert authz_policy.permits(group, ['authority:example.com'], 'write')

    def test_members_writeable(self, group, authz_policy):
        group.writeable_by = WriteableBy.members
        assert authz_policy.permits(group, ['group:test-group'], 'write')

    def test_not_writeable(self, group, authz_policy):
        group.writeable_by = None,
        assert not authz_policy.permits(group, ['authority:example.com', 'group:test-group'], 'write')

    def test_creator_has_admin_permissions(self, group, authz_policy):
        assert authz_policy.permits(group, 'acct:luke@example.com', 'admin')

    def test_no_admin_permission_when_no_creator(self, group, authz_policy):
        group.creator = None

        principals = authz_policy.principals_allowed_by_permission(group, 'admin')
        assert len(principals) == 0

    def test_fallback_is_deny_all(self, group, authz_policy):
        assert not authz_policy.permits(group, [security.Everyone], 'foobar')

    @pytest.fixture
    def authz_policy(self):
        return ACLAuthorizationPolicy()

    @pytest.fixture
    def group(self):
        creator = models.User(username='luke', authority='example.com')
        group = models.Group(name='test-group',
                             authority='example.com',
                             creator=creator)
        group.pubid = 'test-group'
        return group

    def permissions(self, acl):
        return [term[-1] for term in acl]
