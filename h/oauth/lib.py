# -*- coding: utf-8 -*-
"""Library support for OAuth integration."""
from pyramid.util import action_method

from .interfaces import IClientFactory


@action_method
def set_client_factory(config, factory):
    """Override the :term:`client factory` in the current configuration. The
    ``factory`` argument must be support :class:`h.oauth.IClientFactory`
    interface."""
    def register():
        impl = config.maybe_dotted(factory)
        config.registry.registerUtility(impl, IClientFactory)

    intr = config.introspectable('client factory', None,
                                 config.object_description(factory),
                                 'client factory')
    intr['factory'] = factory
    config.action(IClientFactory, register, introspectables=(intr,))


def get_client(request, client_id):
    """Get an :class:`h.oauth.IClient` instance from a client id by using
    the configured :term:`client factory`."""
    registry = request.registry
    factory = registry.getUtility(IClientFactory)
    return factory(client_id)
