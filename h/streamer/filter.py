# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unicodedata

from jsonpointer import resolve_pointer
from h.util.uri import normalize as normalize_uri
from h._compat import text_type

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


class FilterHandler(object):
    def __init__(self, filter_json):
        self.filter = filter_json

    def evaluate_clause(self, clause, target):
        field_value = resolve_pointer(target, clause["field"], None)
        if field_value is None:
            return False

        filter_term = clause["value"]

        def normalize(term):
            # Apply generic normalization.
            normalized = uni_fold(term)

            # Apply field-specific normalization.
            if clause["field"] == "/uri":
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

    def include_any(self, target):
        for clause in self.filter["clauses"]:
            if self.evaluate_clause(clause, target):
                return True
        return False

    def match(self, target, action=None):
        if len(self.filter["clauses"]) > 0:
            return self.include_any(target)
        else:
            return True


def uni_fold(text):
    """
    Return a case-folded and Unicode-normalized copy of ``text``.

    This is used to ensure matching of filters against annotations ignores
    differences in case or different ways of representing the same characters.
    """
    # Convert bytes to text
    if isinstance(text, bytes):
        text = text_type(text, "utf-8")

    # Do not touch other types
    if not isinstance(text, text_type):
        return text

    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join([c for c in text if not unicodedata.combining(c)])
