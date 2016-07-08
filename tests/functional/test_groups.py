# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest


@pytest.mark.functional
def test_group_page_includes_referrer_tag(app, db_session, factories):
    """
    The group read page should include a referrer tag.

    When a logged-in user who is a member of the group visits the group's page,
    the page should include a `<meta name="referrer" ...` tag that asks the
    browser not to send the path part of the page's URL to third-party servers
    in the Referer header when following links on the page.

    This is because the group's URL is secret - if you have it you can join
    the group.
    """
    user = factories.User(password='pass')
    group = factories.Group(creator=user)
    db_session.commit()

    res = app.get('/login')
    res.form['username'] = user.username
    res.form['password'] = 'pass'
    res = res.form.submit()

    res = app.get('/groups/{pubid}/{slug}'.format(pubid=group.pubid,
                                                  slug=group.slug))

    assert res.html.head.find(
        'meta', attrs={'name': 'referrer'}, content='origin')
