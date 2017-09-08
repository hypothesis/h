# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pyramid.renderers


json_sorted_factory = pyramid.renderers.JSON(sort_keys=True)


def includeme(config):
    config.add_renderer(name='json_sorted', factory=json_sorted_factory)
