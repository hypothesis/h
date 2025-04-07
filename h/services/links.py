"""Tools for generating links to domain objects."""

from urllib.parse import urljoin

from pyramid.request import Request

from h.security.request_methods import default_authority


def json_link(request, annotation) -> str:
    return request.route_url("api.annotation", id=annotation.id)


def jsonld_id_link(request, annotation) -> str:
    return request.route_url("annotation", id=annotation.id)


def html_link(request, annotation) -> str | None:
    """Return a link to an HTML representation of the given annotation, or None."""
    is_third_party_annotation = annotation.authority != request.default_authority
    if is_third_party_annotation:
        # We don't currently support HTML representations of third party
        # annotations.
        return None
    return request.route_url("annotation", id=annotation.id)


def incontext_link(request, annotation) -> str | None:
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
    elif uri.startswith("urn:x-pdf:") and annotation.document:  # pragma: no cover
        for docuri in annotation.document.document_uris:
            uri = docuri.uri
            if uri.startswith(("http://", "https://")):
                link += "/" + uri[uri.index("://") + 3 :]
                break

    return link


class LinksService:
    """A service for generating links to annotations."""

    def __init__(self, base_url):
        """
        Create a new links service.

        :param base_url: the base URL for link construction
        :param registry: the registry in which to look up routes
        :type registry: pyramid.registry.Registry
        """
        self.base_url = base_url

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
        self._request = Request.blank("/", base_url=base_url)

        # Allow retrieval of the authority from the fake request object, the
        # same as we do for real requests.
        self._request.set_property(
            default_authority, name="default_authority", reify=True
        )

    def json_link(self, annotation):
        return json_link(self._request, annotation)

    def jsonld_id_link(self, annotation) -> str:
        return jsonld_id_link(self._request, annotation)

    def html_link(self, annotation):
        return html_link(self._request, annotation)

    def incontext_link(self, annotation):
        return incontext_link(self._request, annotation)


def links_factory(_context, request):
    """Return a LinksService instance for the passed context and request."""
    return LinksService(
        base_url=request.registry.settings.get("h.app_url", "http://localhost:5000")
    )
