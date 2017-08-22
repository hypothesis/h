# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import OrderedDict

from h.renderers import json_sorted_factory


class TestSortedJSONRenderer(object):

    def test_sorts_response_keys(self):
        # An OrderedDict makes sure the keys won't end up in order by chance
        data = OrderedDict([('bar', 1), ('foo', 'bang'), ('baz', 5)])
        renderer = json_sorted_factory(info=None)

        result = renderer(data, system={})

        assert result == '{"bar": 1, "baz": 5, "foo": "bang"}'
