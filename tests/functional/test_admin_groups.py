# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services.group import GROUP_TYPES


@pytest.mark.functional
class TestAdminGroupCreate(object):
    """Tests for the /admin/groups/create page."""

    @pytest.mark.parametrize('group_type', GROUP_TYPES.keys())
    def test_can_create_group(self, app, admin_user_and_password, group_type):
        admin_user, admin_user_password = admin_user_and_password
        app = self._login(app, admin_user.username, admin_user_password)
        res = app.get('/admin/groups/create')
        create_group_form = res.forms['admin-group-create-form']
        create_group_form['name'] = 'Public Group for Test'
        create_group_form['description'] = 'description of awesome group'
        create_group_form['group_type'].select(group_type)
        form_submit_res = create_group_form.submit().follow()
        assert form_submit_res.text.startswith('<!DOCTYPE html>')

    def _login(self, app, username, password):
        res = app.get('/login')
        res.form['username'] = username
        res.form['password'] = password
        res.form.submit()
        return app

    @pytest.fixture
    def admin_user_and_password(self, db_session, factories):
        # Password is 'pass'
        password = 'pass'
        user = factories.User(admin=True, username='admin',
                              password='$2b$12$21I1LjTlGJmLXzTDrQA8gusckjHEMepTmLY5WN3Kx8hSaqEEKj9V6')
        db_session.commit()
        return (user, password)
