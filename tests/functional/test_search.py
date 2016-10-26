# -*- coding: utf-8 -*-
"""Functional tests for the /search page, without JavaScript."""

from __future__ import unicode_literals

import pytest

from h import models


@pytest.mark.functional
def test_search_input_text_is_submitted_as_q_without_javascript(app):
    res = app.get('/search')
    form = res.forms['search-bar']
    form['q'] = 'test search query'

    res = res.form.submit()

    assert res.forms['search-bar']['q'].value == 'test search query', (
        "The server should have received the search text in the q parameter, "
        "and echoed it back in the q parameter")


@pytest.fixture(autouse=True)
def enable_search_page_and_activity_pages_feature_flags(
        app,  # This fixture depends on the app fixture so that the app fixture
              # will be run before, not after, this fixture. This is necessary
              # because the app fixture cleans the database which would delete
              # the changes made by this fixture if it were run after this
              # fixture.
        db_session):
    for feature_name in ('search_page', 'activity_pages'):
        assert db_session.query(models.Feature).filter_by(name=feature_name).all() == []
        db_session.add(models.Feature(name=feature_name, everyone=True))
    db_session.commit()
