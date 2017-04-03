# -*- coding: utf-8 -*-


def includeme(config):
    # Register the transform_annotation subscriber so that nipsa fields are
    # written into annotations on save.
    config.add_subscriber('h.nipsa.subscribers.transform_annotation',
                          'h.events.AnnotationTransformEvent')

    # Register an additional filter with the API search module
    config.memex_add_search_filter('h.nipsa.search.Filter')
