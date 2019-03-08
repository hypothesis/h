# -*- coding: utf-8 -*-
"""Helpers for generating and retrieving service link metadata"""

from __future__ import unicode_literals


class ServiceLink(object):
    """Encapsulate metadata about an API service"""

    def __init__(self, name, route_name, method="GET", description=None):
        self.name = name
        self.route_name = route_name
        self.method = method
        self.description = description

    def primary_method(self):
        """
        Determine the primary HTTP method for this service

        If the ``method`` indicated is a tuple, the first entry will be
        returned.

        :rtype: str
        """
        method = self.method
        if isinstance(method, tuple):
            # If the view matches multiple methods, assume the first one is
            # preferred
            method = method[0]
        return method


def register_link(link, versions, registry):
    """
    Register an API service's metadata for its supported versions

    Add an entry for the indicated ``link`` onto the ``registry`` for each
    of the versions it claims to supported. These entries include basic
    endpoint metadata like description and primary HTTP method.

    These data structures are later referenced to deliver an index of our
    API endpoints at `GET /api/`.

    :arg link: The link to add metadata about
    :type link: :class:`~h.views.api.helpers.links.ServiceLink`
    :arg versions: Supported versions (e.g. ``"v1"``)
    :type versions: list(str)
    :arg registry: Pyramid registry to put metadata in; mutated in place
    :type registry: :class:`pyramid.registry.Registry`
    """

    if not hasattr(registry, "api_links"):
        registry.api_links = {}
    for version in versions:
        if version not in registry.api_links:
            registry.api_links[version] = []
        registry.api_links[version].append(link)
