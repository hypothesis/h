"""Helpers for generating and retrieving service link metadata."""


class ServiceLink:
    """Encapsulate metadata about an API service."""

    def __init__(self, name, route_name, method="GET", description=None):
        self.name = name
        self.route_name = route_name
        self.method = method
        self.description = description

    def primary_method(self):
        """
        Determine the primary HTTP method for this service.

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
    Register an API service's metadata for its supported versions.

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


def format_nested_links(api_links, templater):
    """Format API link metadata as nested dicts for V1 variant of API index."""
    formatted_links = {}
    for link in api_links:
        method_info = {
            "method": link.primary_method(),
            "url": templater.route_template(link.route_name),
            "desc": link.description,
        }
        _set_at_path(formatted_links, link.name.split("."), method_info)

    return formatted_links


def _set_at_path(dict_, path, value):
    """
    Set the value at a given `path` within a nested `dict`.

    :param dict_: The root `dict` to update
    :param path: List of path components
    :param value: Value to assign
    """
    key = path[0]
    if key not in dict_:
        dict_[key] = {}

    if len(path) == 1:
        dict_[key] = value
    else:
        _set_at_path(dict_[key], path[1:], value)
