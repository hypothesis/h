# -*- coding: utf-8 -*-

__all__ = ('__version__',)
__version__ = '0.39.0+dev'


def includeme(config):
    config.include('pyramid_services')

    # This must be included first so it can set up the model base class if
    # need be.
    config.include('memex.models')

    config.include('memex.eventqueue')
    config.include('memex.links')
    config.include('memex.presenters')
    config.include('memex.search')
    config.include('memex.views')

    config.add_route('api.index', '/')
    config.add_route('api.annotations', '/annotations')
    config.add_route('api.annotation',
                     '/annotations/{id:[A-Za-z0-9_-]{20,22}}',
                     factory='memex.resources:AnnotationResourceFactory',
                     traverse='/{id}')
    config.add_route('api.annotation.jsonld',
                     '/annotations/{id:[A-Za-z0-9_-]{20,22}}.jsonld',
                     factory='memex.resources:AnnotationResourceFactory',
                     traverse='/{id}')
    config.add_route('api.search', '/search')

    config.register_service_factory('memex.groups.default_group_service_factory',
                                    iface='memex.interfaces.IGroupService')
