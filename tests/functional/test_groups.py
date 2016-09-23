# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest


@pytest.mark.functional
def test_group_page_includes_referrer_tag(app, db_session, factories, user):
    """
    The group read page should include a referrer tag.

    When a logged-in user who is a member of the group visits the group's page,
    the page should include a `<meta name="referrer" ...` tag that asks the
    browser not to send the path part of the page's URL to third-party servers
    in the Referer header when following links on the page.

    This is because the group's URL is secret - if you have it you can join
    the group.
    """
    group = factories.Group(creator=user)
    db_session.commit()

    res = app.get('/groups/{pubid}/{slug}'.format(pubid=group.pubid,
                                                  slug=group.slug))

    assert res.html.head.find(
        'meta', attrs={'name': 'referrer'}, content='origin')


@pytest.mark.functional
def test_submit_create_group_form_without_xhr_returns_full_html_page(app):
    res = app.get('/groups/new')
    group_form = res.forms['deform']
    group_form['name'] = 'My New Group'

    res = group_form.submit().follow()

    assert res.body.startswith('<!DOCTYPE html>')


@pytest.mark.functional
def test_submit_create_group_form_with_xhr_returns_partial_html_snippet(app):
    res = app.get('/groups/new')
    group_form = res.forms['deform']
    group_form['name'] = 'My New Group'

    res = group_form.submit(xhr=True)

    assert res.body.strip('\n').startswith('<form')


@pytest.mark.functional
def test_submit_create_group_form_with_xhr_returns_plain_text(app):
    res = app.get('/groups/new')
    group_form = res.forms['deform']
    group_form['name'] = 'My New Group'

    res = group_form.submit(xhr=True)

    assert res.content_type == 'text/plain'


@pytest.fixture
def user(db_session, factories):
    user = factories.User(authority='localhost', password='pass')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def app(app, user):
    res = app.get('/login')
    res.form['username'] = user.username
    res.form['password'] = 'pass'
    res.form.submit()
    return app
