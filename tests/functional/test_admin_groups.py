# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services.group import GROUP_TYPES
from webtest.forms import Form

authority = 'example.com'


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
    user = factories.User(admin=True, username='admin', authority=authority,
                          password='$2b$12$21I1LjTlGJmLXzTDrQA8gusckjHEMepTmLY5WN3Kx8hSaqEEKj9V6')
    db_session.commit()
    return (user, password)


def _members_res_has_user(res, user):
    all_member_els = res.html.select('[typeof=User]')
    member_el = filter(lambda e: e.select_one(
        '[property=userid]').text == user.userid, all_member_els)
    return member_el


@pytest.mark.functional
class TestAdminGroupMembers(object):
    """Tests for the /admin/groups/{pubid}/{slug}/members page."""

    def test_can_add_member_by_username(self, app, admin_user_and_password, group, user_to_add):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)
        form_submit_res = _add_member(
            app, user_to_add, group, auth_with_fields=('username',))
        members_res = form_submit_res.follow()
        assert _members_res_has_user(members_res, user_to_add)

    def test_can_add_member_by_email(self, app, admin_user_and_password, group, user_to_add):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)
        form_submit_res = _add_member(
            app, user_to_add, group, auth_with_fields=('email',))
        members_res = form_submit_res.follow()
        assert _members_res_has_user(members_res, user_to_add)

    def test_cant_add_by_both_username_and_email(self, app, admin_user_and_password, group, user_to_add):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)
        form_submit_res = _add_member(app, user_to_add, group, auth_with_fields=(
            'email', 'username'), expect_errors=True)
        assert form_submit_res.status_code == 400
        assert not _members_res_has_user(form_submit_res, user_to_add)

    def test_can_remove_member(self, app, admin_user_and_password, group, user_to_add):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)
        add_member_res = _add_member(app, user_to_add, group)
        member = user_to_add
        res = app.get(
            '/admin/groups/{pubid}/{slug}/members/'.format(pubid=group.pubid, slug=group.slug))
        all_member_els = res.html.select('[typeof=User]')
        member_el = filter(lambda e: e.select_one(
            '[property=userid]').text == member.userid, all_member_els)
        assert member_el
        remove_member_el = member_el[0].select_one(
            '.test-TestAdminGroupMembers__remove-member')
        assert remove_member_el
        remove_member_form_el = remove_member_el.select_one('form')
        remove_member_form = Form(res, unicode(remove_member_form_el))
        remove_member_res = remove_member_form.submit()
        members_res = remove_member_res.follow()
        assert not _members_res_has_user(members_res, member)

    @pytest.fixture
    def group(self, db_session, factories):
        group = factories.Group(
            name=u'TestAdminGroupMember', authority=authority)
        db_session.commit()
        return group

    @pytest.fixture
    def user_to_add(self, db_session, factories):
        user = factories.User(
            username='member', authority=authority, email='member@email.com')
        db_session.commit()
        return user


def _logout(app):
    app.get('/logout')


def _add_member(app, user_to_add, group, auth_with_fields=('email',), expect_errors=False):
    admin_group_members_url = '/admin/groups/{pubid}/{slug}/members/'.format(
        pubid=group.pubid, slug=group.slug)
    res = app.get(admin_group_members_url)
    add_member_form = res.forms['admin-group-add-member-form']
    for field in auth_with_fields:
        add_member_form[field] = getattr(user_to_add, field)
    form_submit_res = add_member_form.submit(expect_errors=expect_errors)
    return form_submit_res
