# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class TestInvalidPathTweenFactory(object):
    def test_it_400s_if_the_requested_path_isnt_utf8(self, app):
        app.get("/%c5", status=400)
