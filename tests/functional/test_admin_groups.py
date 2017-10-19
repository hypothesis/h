# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services.group import GROUP_TYPES

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


@pytest.mark.functional
class TestAdminGroupMembers(object):
    """Tests for the /admin/groups/{pubid}/{slug}/members page."""

    def test_can_add_member_by_username(self, app, admin_user_and_password, group, user_to_add):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)
        admin_group_members_url = '/admin/groups/{pubid}/{slug}/members/'.format(
            pubid=group.pubid, slug=group.slug)
        res = app.get(admin_group_members_url)
        add_member_form = res.forms['admin-group-add-member-form']
        add_member_form['username'] = user_to_add.username
        form_submit_res = add_member_form.submit().follow()

    def test_can_add_member_by_email(self, app, admin_user_and_password, group, user_to_add):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)
        admin_group_members_url = '/admin/groups/{pubid}/{slug}/members/'.format(
            pubid=group.pubid, slug=group.slug)
        res = app.get(admin_group_members_url)
        add_member_form = res.forms['admin-group-add-member-form']
        add_member_form['email'] = user_to_add.email
        form_submit_res = add_member_form.submit().follow()

    def test_cant_add_by_both_username_and_email(self, app, admin_user_and_password, group, user_to_add):
        admin_user, admin_user_password = admin_user_and_password
        app = _login(app, admin_user.username, admin_user_password)
        admin_group_members_url = '/admin/groups/{pubid}/{slug}/members/'.format(
            pubid=group.pubid, slug=group.slug)
        res = app.get(admin_group_members_url)
        add_member_form = res.forms['admin-group-add-member-form']
        add_member_form['email'] = user_to_add.email
        add_member_form['username'] = user_to_add.username
        form_submit_res = add_member_form.submit(expect_errors=True)
        assert form_submit_res.status_code == 400

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
