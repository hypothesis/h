# -*- coding: utf-8 -*-
"""Functional tests for the /search page, without JavaScript."""

from __future__ import unicode_literals

import pytest


@pytest.mark.functional
def test_search_input_text_is_submitted_as_q_without_javascript(app):
    res = app.get("/search")
    form = res.forms["search-bar"]
    form["q"] = "test search query"

    res = res.form.submit()

    assert res.forms["search-bar"]["q"].value == "test search query", (
        "The server should have received the search text in the q parameter, "
        "and echoed it back in the q parameter"
    )
