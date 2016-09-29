# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.models import Token


class TestToken(object):
    def test_init_generates_value(self):
        assert Token().value
