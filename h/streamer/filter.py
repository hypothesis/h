# -*- coding: utf-8 -*-

from h.util.uri import normalize as normalize_uri

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
    @classmethod
    def matching(cls, sockets, annotation):
        """Find sockets with matching filters for the given annotation.

        For this to work, the sockets must have first had `set_filter()` called
        on them.

        :param sockets: Iterable of sockets to check
        :param annotation: Annotation to match
        :return: A generator of matching socket objects
        """
        values = {
            "/id": [annotation.id],
            "/uri": [normalize_uri(annotation.target_uri)],
            "/references": set(annotation.references),
        }

        for socket in sockets:
            # Some sockets might not yet have the filter applied (or had a non
            # parsable filter etc.)
            if not hasattr(socket, "filter_rows"):
                continue

            # Iterate over the filter_rows added by `set_filter()`
            for field, value in socket.filter_rows:
                if value in values[field]:
                    yield socket
                    break

    @classmethod
    def set_filter(cls, socket, filter):
        """Add filtering information to a socket for use with `matching()`.

        :param socket: Socket to add filtering information too
        :param filter: Filter JSON to process
        """
        socket.filter_rows = tuple(cls._rows_for(filter))

    @classmethod
    def _rows_for(cls, filter):
        """Convert a filter to field value pairs."""
        for clause in filter["clauses"]:
            values = clause["value"]

            # Normalise to an iterable of distinct values
            values = set(values) if isinstance(values, list) else [values]

            field = clause["field"]

            for value in values:
                if field == "/uri":
                    value = normalize_uri(value)

                yield field, value
