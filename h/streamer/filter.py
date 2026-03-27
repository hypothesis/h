from h import storage
from h.util.uri import build_scope_key, normalize as normalize_uri, parse_uri_versions

FILTER_SCHEMA = {
    "type": "object",
    "properties": {
        # Ignored, but kept here for backwards compatibility.
        "match_policy": {"type": "string", "enum": ["include_any"]},
        # Ignored, but kept here for backwards compatibility.
        "actions": {
            "create": {"type": "boolean", "default": True},
            "update": {"type": "boolean", "default": True},
            "delete": {"type": "boolean", "default": True},
        },
        "clauses": {
            "type": "array",
            "items": {
                "field": {"type": "string", "format": "json-pointer"},
                "operator": {"type": "string", "enum": ["equals", "one_of"]},
                "value": "object",
            },
        },
    },
    "required": ["match_policy", "clauses", "actions"],
}


class SocketFilter:
    KNOWN_FIELDS = {"/id", "/group", "/uri", "/references"}  # noqa: RUF012

    @classmethod
    def matching(cls, sockets, annotation, session):
        """
        Find sockets with matching filters for the given annotation.

        For this to work, the sockets must have first had `set_filter()` called
        on them.

        :param sockets: Iterable of sockets to check
        :param annotation: Annotation to match
        :param session: DB session

        :return: A generator of matching socket objects
        """

        # Expand the URI to ensure we match any variants of it. This should
        # match the normalization when searching (see `h.search.query`)
        expanded_uris = set(
            storage.expand_uri(session, annotation.target_uri, normalized=True)
        )
        # Versioned annotations only match clients filtering by that version.
        # Unversioned annotations only match clients without version filter.
        if annotation.version:
            uri_scope_keys = {
                build_scope_key(uri, annotation.version) for uri in expanded_uris
            }
        else:
            uri_scope_keys = set(expanded_uris)

        values = {
            "/id": [annotation.id],
            "/group": [annotation.groupid],
            "/uri": uri_scope_keys,
            "/references": set(annotation.references),
        }

        for socket in sockets:
            # Some sockets might not yet have the filter applied (or had a non
            # parsable filter etc.)
            if not hasattr(socket, "filter_rows"):
                continue

            # Iterate over the filter_rows added by `set_filter()`
            for field, value in socket.filter_rows:
                try:
                    if value in values[field]:
                        yield socket
                        break
                except KeyError:
                    continue

    @classmethod
    def set_filter(cls, socket, filter_):
        """
        Add filtering information to a socket for use with `matching()`.

        :param socket: Socket to add filtering information too
        :param filter_: Filter JSON to process
        """
        socket.filter_rows = tuple(cls._rows_for(filter_))

    @classmethod
    def _rows_for(cls, filter_):
        """Convert a filter to field value pairs."""
        for clause in filter_["clauses"]:
            field = clause["field"]
            if field not in cls.KNOWN_FIELDS:
                continue

            values = clause["value"]

            # Normalize to an iterable of distinct values
            values = set(values) if isinstance(values, list) else [values]

            for value in values:
                if field == "/uri":
                    base_uri, versions = parse_uri_versions(value)
                    value = normalize_uri(base_uri)
                    if versions:
                        for version in versions:
                            yield field, build_scope_key(value, version)
                        continue

                yield field, value
