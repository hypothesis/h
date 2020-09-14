# -*- coding: utf-8 -*-

import unicodedata

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

    def evaluate_clause(self, clause, annotation):
        clause_filter = self._get_filter(clause)

        if clause_filter is None:
            return None

        return clause_filter(annotation)

    def include_any(self, annotation):
        for clause_filter in self._clause_filters:
            if clause_filter(annotation):
                return True

        return False

    def match(self, annotation):
        if not self._clause_filters:
            return True

        return self.include_any(annotation)

    @classmethod
    def _get_filter(cls, clause):
        def clause_filter(annotation):
            field_path = clause["field"]

            # Extract the annotation property that corresponds to the "field"
            # path in the filter. This only supports a small set of paths
            # which are actually used by the Hypothesis client.
            field_value = None
            if field_path == "/uri":
                field_value = annotation.target_uri
            elif field_path == "/references":
                field_value = annotation.references
            elif field_path == "/id":
                field_value = annotation.id

            if field_value is None:
                return False

            filter_term = clause["value"]

            def normalize(term):
                # Apply generic normalization.
                normalized = uni_fold(term)

                # Apply field-specific normalization.
                if field_path == "/uri":
                    normalized = normalize_uri(term)

                return normalized

            if isinstance(filter_term, list):
                filter_term = [normalize(t) for t in filter_term]
            else:
                filter_term = normalize(filter_term)

            if isinstance(field_value, list):
                field_value = [normalize(v) for v in field_value]
            else:
                field_value = normalize(field_value)

            if clause["operator"] == "one_of":
                # The `one_of` operator behaves differently depending on whether
                # the annotation's field value is a list (eg. tags) or atom (eg. id).
                #
                # This is not ideal but the client currently relies on it.
                if isinstance(field_value, list):
                    return filter_term in field_value
                else:
                    return field_value in filter_term
            else:
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
