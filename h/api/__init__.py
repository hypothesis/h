# -*- coding: utf-8 -*-


def includeme(config):
    config.include('h.api.db')
    config.include('h.api.presenters')
    config.include('h.api.search')
    config.include('h.api.views')

    config.add_route('api.index', '/')
    config.add_route('api.annotations', '/annotations')
    config.add_route('api.annotation',
                     '/annotations/{id:[A-Za-z0-9_-]{20,22}}',
                     factory='h.api.resources:AnnotationFactory',
                     traverse='/{id}')
    config.add_route('api.annotation.jsonld',
                     '/annotations/{id:[A-Za-z0-9_-]{20,22}}.jsonld',
                     factory='h.api.resources:AnnotationFactory',
                     traverse='/{id}')
    config.add_route('api.search', '/search')
