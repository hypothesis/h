# -*- coding: utf-8 -*-


def includeme(config):
    config.include('h.api.db')
    config.include('h.api.search')
    config.include('h.api.views')

    config.add_route('api.index', '/')
    config.add_route('api.annotations', '/annotations')
    config.add_route('api.annotation',
                     '/annotations/{id}',
                     factory='h.api.resources:AnnotationFactory',
                     traverse='/{id}')
    config.add_route('api.search', '/search')
