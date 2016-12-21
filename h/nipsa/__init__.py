# -*- coding: utf-8 -*-

from h.nipsa import search


def includeme(config):
    # Register the transform_annotation subscriber so that nipsa fields are
    # written into annotations on save.
    config.add_subscriber('h.nipsa.subscribers.transform_annotation',
                          'memex.events.AnnotationTransformEvent')

    # Register an additional filter with the API search module
    config.add_search_filter(search.Filter)
