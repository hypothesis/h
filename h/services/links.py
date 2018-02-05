# -*- coding: utf-8 -*-

"""Tools for generating links to domain objects. """

from __future__ import unicode_literals

from pyramid.request import Request

from h.auth import authority

LINK_GENERATORS_KEY = 'h.links.link_generators'


class LinksService(object):

    """A service for generating links to annotations."""

    def __init__(self, base_url, registry):
        """
        Create a new links service.

        :param base_url: the base URL for link construction
        :param registry: the registry in which to look up routes
        :type registry: pyramid.registry.Registry
        """
        self.base_url = base_url
        self.registry = registry

        # It would be absolutely fair if at this point you asked yourself any
        # of the following questions:
        #
        # - Why are we constructing a fake request here?
        # - Didn't we have a request and then discard it in the service
        #   factory?
        # - This looks really janky!
        #
        # Well, apart from the fact that the last one there isn't a question,
        # those are good questions. The reason for doing this is that we need
        # to be able to generate links to annotations in situations where we
        # don't necessarily have a request object around, such as in the
        # WebSocket server, or in a CLI command.
        #
        # In these situations, it should suffice to have an application
        # registry (for the routing table) and a base URL. The reason we
        # generate a request object is that this is the simplest and least
        # error-prone way to get access to the route_url function, which can
        # be used by link generators.
        self._request = Request.blank('/', base_url=base_url)
        self._request.registry = registry

        # Allow retrieval of the authority from the fake request object, the
        # same as we do for real requests.
        self._request.set_property(authority, name='authority', reify=True)

    def get(self, annotation, name):
        """Get the link named `name` for the passed `annotation`."""
        g, _ = self.registry[LINK_GENERATORS_KEY][name]
        return g(self._request, annotation)

    def get_all(self, annotation):
        """Get all (non-hidden) links for the passed `annotation`."""
        links = {}
        for name, (g, hidden) in self.registry[LINK_GENERATORS_KEY].items():
            if hidden:
                continue
            link = g(self._request, annotation)
            if link is not None:
                links[name] = link
        return links


def links_factory(context, request):
    """Return a LinksService instance for the passed context and request."""
    base_url = request.registry.settings.get('h.app_url',
                                             'http://localhost:5000')
    return LinksService(base_url=base_url,
                        registry=request.registry)


def add_annotation_link_generator(config, name, generator, hidden=False):
    """
    Registers a function which generates a named link for an annotation.

    Annotation hypermedia links are added to the rendered annotations in a
    `links` property or similar. `name` is the unique identifier for the link
    type, and `generator` is a callable which accepts two arguments -- the
    current request, and the annotation for which to generate a link -- and
    returns a string.

    If `hidden` is True, then the link generator will not be included in the
    default links output when rendering annotations.
    """
    registry = config.registry
    if LINK_GENERATORS_KEY not in registry:
        registry[LINK_GENERATORS_KEY] = {}
    registry[LINK_GENERATORS_KEY][name] = (generator, hidden)
