# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pyramid.renderers


json_sorted_factory = pyramid.renderers.JSON(sort_keys=True)


class SVGRenderer(object):
    def __init__(self, info):
        pass

    def __call__(self, value, system):
        request = system.get('request')
        if request is not None:
            response = request.response
            ct = response.content_type
            if ct == response.default_content_type:
                response.content_type = 'image/svg+xml'

        return value

def includeme(config):
    config.add_renderer(name='json_sorted', factory=json_sorted_factory)
    config.add_renderer(name='svg', factory=SVGRenderer)
