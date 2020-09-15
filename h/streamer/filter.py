# -*- coding: utf-8 -*-

import unicodedata
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


class FilterHandler:
    FIELD_GETTERS = {
        "/uri": attrgetter("target_uri"),
        "/references": attrgetter("references"),
        "/id": attrgetter("id"),
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
            field_getter = cls.FIELD_GETTERS[field_path]
        except KeyError:
            return

        def normalize(term, known_term=False):
            if not known_term and isinstance(term, list):
                return [normalize(sub_term, known_term=True) for sub_term in term]

            # Notice closure around field_path here
            if field_path == "/uri":
                # Apply field-specific normalization.
                return normalize_uri(term)

            # Apply generic normalization.
            return uni_fold(term)

        filter_term = normalize(clause["value"])

        def clause_filter(annotation):
            # Extract the annotation property that corresponds to the "field"
            # path in the filter.
            field_value = field_getter(annotation)

            if field_value is None:
                return False

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


def uni_fold(text):
    """
    Return a case-folded and Unicode-normalized copy of ``text``.

    This is used to ensure matching of filters against annotations ignores
    differences in case or different ways of representing the same characters.
    """
    # Convert bytes to text
    if isinstance(text, bytes):
        text = str(text, "utf-8")

    # Do not touch other types
    if not isinstance(text, str):
        return text

    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join([c for c in text if not unicodedata.combining(c)])
