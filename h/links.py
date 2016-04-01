# -*- coding: utf-8 -*-

"""
Provides links to different representations of annotations.
"""


from h._compat import urlparse


def html_link(request, annotation):
    """Generate a link to an HTML representation of an annotation."""
    return request.route_url('annotation', id=annotation.id)


def incontext_link(request, annotation):
    """Generate a link to an annotation on the page where it was made."""
    if not request.feature('direct_linking'):
        return None

    bouncer_url = request.registry.settings.get('h.bouncer_url')
    if not bouncer_url:
        return None
    return urlparse.urljoin(bouncer_url, annotation.id)


def includeme(config):
    # Add an annotation link generator for the `annotation` view -- this adds a
    # named link called "html" to API rendered views of annotations. See
    # :py:mod:`h.api.presenters` for details.
    config.add_annotation_link_generator('html', html_link)

    # Add an annotation link generator for viewing annotations in context on
    # the page on which they were made.
    config.add_annotation_link_generator('incontext', incontext_link)
