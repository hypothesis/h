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
    config.include('memex.search')

    config.register_service_factory('memex.groups.default_group_service_factory',
                                    iface='memex.interfaces.IGroupService')
