# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest


@pytest.mark.functional
def test_atom_feed(app):
    app.get("/stream.atom")


@pytest.mark.functional
def test_rss_feed(app):
    app.get("/stream.rss")
