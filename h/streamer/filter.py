# -*- coding: utf-8 -*-

from functools import lru_cache
from operator import attrgetter

from h.util.uri import normalize as normalize_uri

SCHEMA = {
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


def _normalize_uri_multi(items):
    """
    Normalise uri's for comparison.

    :param items: A list or single item
    :return: A list of mapped values, or a single value (if passed)
    """
    if isinstance(items, list):
        return [normalize_uri(item) for item in items]

    return normalize_uri(items)


class FilterHandler:
    FIELDS = {
        # Fields we accept mapped to a getter, and a normalization function
        "/uri": [attrgetter("target_uri"), _normalize_uri_multi],
        "/references": [attrgetter("references"), None],
        "/id": [attrgetter("id"), None],
    }

    def __init__(self, filter_json):
        self.filter = filter_json

        # Pre-compile as much as is sensible about our filters, so we can do
        # this work once, and then apply it over and over
        self._clause_filters = [
            clause_filter
            for clause_filter in (
                self._get_filter(clause) for clause in self.filter.get("clauses", [])
            )
            if clause_filter
        ]

    def match(self, annotation):
        if not self._clause_filters:
            return True

        for clause_filter in self._clause_filters:
            if clause_filter(annotation):
                return True

        return False

    @classmethod
    def _get_filter(cls, clause):
        """Get a filter function for a given clause.

        :param clause: The decoded JSON clause
        :return: A function which accepts an annotation and returns a truth
            value depending on whether the value applies
        """
        field_path = clause["field"]

        try:
            field_getter, normalize = cls.FIELDS[field_path]
        except KeyError:
            return

        filter_term = clause["value"]
        if normalize is not None:
            filter_term = normalize(filter_term)

        def clause_filter(annotation):
            # Extract the annotation property that corresponds to the "field"
            # path in the filter.
            field_value = field_getter(annotation)

            if field_value is None:
                return False

            if normalize:
                field_value = normalize(field_value)

            if clause["operator"] == "one_of":
                # The `one_of` operator behaves differently depending on
                # whether the annotation's field value is a list (eg. tags)
                # or atom (eg. id). This is not ideal but the client currently
                # relies on it.
                if isinstance(field_value, list):
                    return filter_term in field_value

                return field_value in filter_term

            return field_value == filter_term

        return clause_filter


class NormalizedAnnotation:
    """A normalized and caching version of an annotation.

    This version proxies, normalises and caches the fields used in the filter
    algorithm to speed up processing. The result can be quite dramatic over
    a large number of clients.

    The intended use is to wrap an annotation before passing to a filter
    `match()` method.
    """

    def __init__(self, annotation):
        self._annotation = annotation

    @property
    @lru_cache(1)
    def target_uri(self):
        return normalize_uri(self._annotation.target_uri)

    @property
    @lru_cache(1)
    def references(self):
        # Ids require no normalisation, so just pass through
        return self._annotation.references

    @property
    @lru_cache(1)
    def id(self):
        # Ids require no normalisation, so just pass through
        return self._annotation.id
