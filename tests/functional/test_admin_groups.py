# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
import random
import string

from h.services.group import GROUP_TYPES
from webtest.forms import Form

DEFAULT_AUTHORITY = 'example.com'


def randomstr(n): return ''.join(
    [random.choice(string.lowercase) for i in range(n)])


@pytest.mark.functional
class TestAdminGroupCreate(object):
    """Tests for the /admin/groups/create page."""

    @pytest.mark.parametrize('group_type', GROUP_TYPES.keys())
    def test_can_create_group(self, app, admin_user_and_password, group_type):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)
        res = app.get('/admin/groups/create')
        create_group_form = res.forms['admin-group-create-form']
        create_group_form['name'] = 'Public Group for Test'
        create_group_form['description'] = 'description of awesome group'
        create_group_form['group_type'].select(group_type)
        form_submit_res = create_group_form.submit().follow()
        assert form_submit_res.text.startswith('<!DOCTYPE html>')


def _login(app, username, password):
    res = app.get('/login')
    res.form['username'] = username
    res.form['password'] = password
    res.form.submit()
    return app


@pytest.fixture
def admin_user_and_password(db_session, factories):
    # Password is 'pass'
    password = 'pass'
    user = factories.User(admin=True, username='admin', authority=DEFAULT_AUTHORITY,
                          password='$2b$12$21I1LjTlGJmLXzTDrQA8gusckjHEMepTmLY5WN3Kx8hSaqEEKj9V6')
    db_session.commit()
    return (user, password)


def _group_read_res_has_user(res, user):
    all_member_els = res.html.select('[typeof=User]')
    member_el = filter(lambda e: e.select_one(
        '[property=userid]').text.strip() == user.userid, all_member_els)
    return member_el


@pytest.mark.functional
class TestAdminGroupRead(object):
    """
    Tests for the /admin/groups/{pubid}/{slug}/members page.
    """

    def test_cant_add_no_one(self, app, admin_user_and_password, group):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)
        form_submit_res = _add_members(app, '', group, expect_errors=True)
        assert form_submit_res.status_code == 400

    def test_can_add_member_by_username(self, app, admin_user_and_password, group, user_to_add):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)
        form_submit_res = _add_members(app, user_to_add.username, group)
        group_read_res = form_submit_res.follow()
        assert _group_read_res_has_user(group_read_res, user_to_add)

    def test_can_add_member_by_email(self, app, admin_user_and_password, group, user_to_add):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)
        form_submit_res = _add_members(app, user_to_add.email, group)
        group_read_res = form_submit_res.follow()
        assert _group_read_res_has_user(group_read_res, user_to_add)

    def test_can_add_same_user_by_both_username_and_email(self, app, admin_user_and_password, group, user_to_add):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)
        form_submit_res = _add_members(app, ','.join(
            [user_to_add.username, user_to_add.email]), group)
        assert _group_read_res_has_user(form_submit_res.follow(), user_to_add)

    def test_can_add_multiple_users(self, app, admin_user_and_password, group, create_user):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)

        def create_users(n): return [create_user() for user in range(n)]
        # end-user should be able to delmit user identifiers with any of these
        delimiters = [' ', ',', '\n']
        # end-user can identify a user to add by any of these user model fields
        fields = ['username', 'email']
        users_to_add_by = dict(delimiter=dict([d, create_users(2)] for d in delimiters),
                               field=dict([field, create_users(2)] for field in fields),)
        users_to_add = [user for add_by_value in users_to_add_by.values(
        ) for users in add_by_value.values() for user in users]

        add_members_str = '\n'.join(
            # fields
            [user_str
             for field, users in users_to_add_by['field'].items()
             for user_str in map(lambda u: getattr(u, field), users)]
            +
            # delimiters
            [d.join(map(lambda u: u.username, users))
             for d, users in users_to_add_by['delimiter'].items()],
        )
        form_submit_res = _add_members(app, add_members_str, group)

        group_read_res = form_submit_res.follow()
        for user in users_to_add:
            assert _group_read_res_has_user(group_read_res, user)

    def test_can_remove_member(self, app, admin_user_and_password, group, user_to_add):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)
        _add_members(app, user_to_add.username, group)
        member = user_to_add
        res = app.get(
            '/admin/groups/{pubid}/{slug}/'.format(pubid=group.pubid, slug=group.slug))
        all_member_els = res.html.select('[typeof=User]')
        member_el = filter(lambda e: e.select_one(
            '[property=userid]').text.strip() == member.userid, all_member_els)
        assert member_el
        remove_member_el = member_el[0].select_one(
            '.test-TestAdminGroupRead__remove-member')
        assert remove_member_el
        remove_member_form_el = remove_member_el.select_one('form')
        remove_member_form = Form(res, str(remove_member_form_el))
        remove_member_res = remove_member_form.submit()
        group_read_res = remove_member_res.follow()
        assert not _group_read_res_has_user(group_read_res, member)

    def test_cant_add_user_from_other_authority(self, app, admin_user_and_password, group, create_user):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)
        authority_b_user = create_user(authority='bengo.is')
        form_submit_res = _add_members(
            app, authority_b_user.email, group, expect_errors=True)
        assert form_submit_res.status_code == 400

    @pytest.fixture
    def group(self, db_session, factories):
        group = factories.Group(
            name=u'TestAdminGroupMember', authority=DEFAULT_AUTHORITY)
        db_session.commit()
        return group

    @pytest.fixture
    def user_to_add(self, create_user):
        return create_user(username='user_to_add')

    @pytest.fixture
    def create_user(self, db_session, factories):
        def create_user(*args, **kwargs):
            kwargs = kwargs.copy()
            username = kwargs.setdefault('username', randomstr(16))
            kwargs.setdefault('authority', DEFAULT_AUTHORITY)
            kwargs.setdefault(
                'email', '{username}@email.com'.format(username=username))
            user = factories.User(**kwargs)
            db_session.commit()
            return user
        return create_user


def _logout(app):
    app.get('/logout')


def _add_members(app, members_str, group, expect_errors=False):
    admin_group_url = '/admin/groups/{pubid}/{slug}/'.format(
        pubid=group.pubid, slug=group.slug)
    res = app.get(admin_group_url)
    add_member_form = res.forms['admin-group-add-member-form']
    add_member_form['user_identifiers'] = members_str
    form_submit_res = add_member_form.submit(expect_errors=expect_errors)
    return form_submit_res

# Useful with AddMemberByUsernameOrEmailSchema


def _add_member(app, user_to_add, group, auth_with_fields=('email',), expect_errors=False):
    admin_group_url = '/admin/groups/{pubid}/{slug}/'.format(
        pubid=group.pubid, slug=group.slug)
    res = app.get(admin_group_url)
    add_member_form = res.forms['admin-group-add-member-form']
    for field in auth_with_fields:
        add_member_form[field] = getattr(user_to_add, field)
    form_submit_res = add_member_form.submit(expect_errors=expect_errors)
    return form_submit_res
