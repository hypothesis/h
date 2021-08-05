"""Provides links to different representations of annotations."""
from urllib.parse import unquote, urljoin, urlparse


def pretty_link(url):
    """
    Return a nicely formatted version of a URL.

    This strips off 'visual noise' from the URL including common schemes
    (HTTP, HTTPS), domain prefixes ('www.') and query strings.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        return url
    netloc = parsed.netloc
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return unquote(netloc + parsed.path)


def html_link(request, annotation):
    """Return a link to an HTML representation of the given annotation, or None."""
    is_third_party_annotation = annotation.authority != request.default_authority
    if is_third_party_annotation:
        # We don't currently support HTML representations of third party
        # annotations.
        return None
    return request.route_url("annotation", id=annotation.id)


def incontext_link(request, annotation):
    """Generate a link to an annotation on the page where it was made."""
    bouncer_url = request.registry.settings.get("h.bouncer_url")
    if not bouncer_url:
        return None

    link = urljoin(bouncer_url, annotation.thread_root_id)
    uri = annotation.target_uri
    if uri.startswith(("http://", "https://")):
        # We can't use urljoin here, because if it detects the second argument
        # is a URL it will discard the base URL, breaking the link entirely.
        link += "/" + uri[uri.index("://") + 3 :]
    elif uri.startswith("urn:x-pdf:") and annotation.document:
        for docuri in annotation.document.document_uris:
            uri = docuri.uri
            if uri.startswith(("http://", "https://")):
                link += "/" + uri[uri.index("://") + 3 :]
                break

    return link


def json_link(request, annotation):
    return request.route_url("api.annotation", id=annotation.id)


def jsonld_id_link(request, annotation):
    return request.route_url("annotation", id=annotation.id)


def includeme(config):
    # Add an annotation link generator for the `annotation` view -- this adds a
    # named link called "html" to API rendered views of annotations. See
    # :py:mod:`h.presenters` for details.
    config.add_annotation_link_generator("html", html_link)

    # Add an annotation link generator for viewing annotations in context on
    # the page on which they were made.
    config.add_annotation_link_generator("incontext", incontext_link)

    # Add a default 'json' link type
    config.add_annotation_link_generator("json", json_link)

    # Add a 'jsonld_id' link type for generating the "id" field for JSON-LD
    # annotations. This is hidden, and so not rendered in the annotation's
    # "links" field.
    config.add_annotation_link_generator("jsonld_id", jsonld_id_link, hidden=True)
