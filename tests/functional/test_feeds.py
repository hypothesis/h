# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def test_atom_feed(app):
    app.get("/stream.atom")


def test_rss_feed(app):
    app.get("/stream.rss")
