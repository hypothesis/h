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
    bouncer_url = request.registry.settings.get('h.bouncer_url')
    if not bouncer_url:
        return None

    link = urlparse.urljoin(bouncer_url, annotation.thread_root_id)
    uri = annotation.target_uri
    if uri.startswith(('http://', 'https://')):
        # We can't use urljoin here, because if it detects the second argument
        # is a URL it will discard the base URL, breaking the link entirely.
        link += '/' + uri[uri.index('://')+3:]
    elif uri.startswith('urn:x-pdf:') and annotation.document:
        for docuri in annotation.document.document_uris:
            uri = docuri.uri
            if uri.startswith(('http://', 'https://')):
                link += '/' + uri[uri.index('://')+3:]
                break

    return link


def includeme(config):
    # Add an annotation link generator for the `annotation` view -- this adds a
    # named link called "html" to API rendered views of annotations. See
    # :py:mod:`h.api.presenters` for details.
    config.add_annotation_link_generator('html', html_link)

    # Add an annotation link generator for viewing annotations in context on
    # the page on which they were made.
    config.add_annotation_link_generator('incontext', incontext_link)
