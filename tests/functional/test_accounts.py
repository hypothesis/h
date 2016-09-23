# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest


@pytest.mark.functional
class TestAccountSettings(object):
    """Tests for the /account/settings page."""

    def test_submit_email_form_without_xhr_returns_full_html_page(self, app):
        res = app.get('/account/settings')

        email_form = res.forms['email']
        email_form['email'] = 'new_email@example.com'
        email_form['email_confirm'] = 'new_email@example.com'
        email_form['password'] = 'pass'

        res = email_form.submit().follow()

        assert res.body.startswith('<!DOCTYPE html>')

    def test_submit_email_form_with_xhr_returns_partial_html_snippet(self,
                                                                     app):
        res = app.get('/account/settings')

        email_form = res.forms['email']
        email_form['email'] = 'new_email@example.com'
        email_form['email_confirm'] = 'new_email@example.com'
        email_form['password'] = 'pass'

        res = email_form.submit(xhr=True, status=200)

        assert res.body.strip('\n').startswith('<form')

    def test_submit_email_form_with_xhr_returns_plain_text(self, app):
        res = app.get('/account/settings')

        email_form = res.forms['email']
        email_form['email'] = 'new_email@example.com'
        email_form['email_confirm'] = 'new_email@example.com'
        email_form['password'] = 'pass'

        res = email_form.submit(xhr=True)

        assert res.content_type == 'text/plain'

    def test_submit_invalid_email_form_with_xhr_returns_400(self, app):
        res = app.get('/account/settings')

        email_form = res.forms['email']
        email_form['email'] = 'new_email@example.com'
        email_form['email_confirm'] = 'WRONG'
        email_form['password'] = 'pass'

        email_form.submit(xhr=True, status=400)

    def test_submit_password_form_without_xhr_returns_full_html_page(self,
                                                                     app):
        res = app.get('/account/settings')

        password_form = res.forms['password']
        password_form['password'] = 'pass'
        password_form['new_password'] = 'new_password'
        password_form['new_password_confirm'] = 'new_password'

        res = password_form.submit().follow()

        assert res.body.startswith('<!DOCTYPE html>')

    def test_submit_password_form_with_xhr_returns_partial_html_snippet(self,
                                                                        app):
        res = app.get('/account/settings')

        password_form = res.forms['password']
        password_form['password'] = 'pass'
        password_form['new_password'] = 'new_password'
        password_form['new_password_confirm'] = 'new_password'

        res = password_form.submit(xhr=True)

        assert res.body.strip('\n').startswith('<form')

    def test_submit_password_form_with_xhr_returns_plain_text(self, app):
        res = app.get('/account/settings')

        password_form = res.forms['password']
        password_form['password'] = 'pass'
        password_form['new_password'] = 'new_password'
        password_form['new_password_confirm'] = 'new_password'

        res = password_form.submit(xhr=True)

        assert res.content_type == 'text/plain'

    def test_submit_invalid_password_form_with_xhr_returns_400(self, app):
        res = app.get('/account/settings')

        password_form = res.forms['password']
        password_form['password'] = 'pass'
        password_form['new_password'] = 'new_password'
        password_form['new_password_confirm'] = 'WRONG'

        password_form.submit(xhr=True, status=400)

    @pytest.fixture
    def user(self, db_session, factories):
        user = factories.User(authority='localhost', password='pass')
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def app(self, app, user):
        res = app.get('/login')
        res.form['username'] = user.username
        res.form['password'] = 'pass'
        res.form.submit()
        return app
