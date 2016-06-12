# -*- coding: utf-8 -*-

from h.nipsa.logic import index
from h.nipsa.logic import add_nipsa
from h.nipsa.logic import remove_nipsa
from h.nipsa import services
from h.nipsa import search

__all__ = ('index', 'add_nipsa', 'remove_nipsa')


def includeme(config):
    # Register the transform_annotation subscriber so that nipsa fields are
    # written into annotations on save.
    config.add_subscriber('h.nipsa.subscribers.transform_annotation',
                          'h.api.events.AnnotationTransformEvent')

    # Register the NIPSA service
    config.register_service_factory(services.nipsa_factory, name='nipsa')

    # Register an additional filter with the API search module
    config.add_search_filter(search.Filter)
