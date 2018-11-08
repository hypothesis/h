# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import unicodedata

from jsonpointer import resolve_pointer
from h._compat import text_type

SCHEMA = {
    "type": "object",
    "properties": {
        # Ignored, but kept here for backwards compatibility.
        "match_policy": {
            "type": "string",
            "enum": ["include_any"]
        },

        # Ignored, but kept here for backwards compatibility.
        "actions": {
            "create": {"type": "boolean", "default":  True},
            "update": {"type": "boolean", "default":  True},
            "delete": {"type": "boolean", "default":  True},
        },

        "clauses": {
            "type": "array",
            "items": {
                "field": {"type": "string", "format": "json-pointer"},
                "operator": {
                    "type": "string",
                    "enum": ["equals", "one_of"]
                },
                "value": "object",
            }
        },
    },
    "required": ["match_policy", "clauses", "actions"]
}


class FilterHandler(object):
    def __init__(self, filter_json):
        self.filter = filter_json

    def evaluate_clause(self, clause, target):
        field_value = resolve_pointer(target, clause['field'], None)
        if field_value is None:
            return False

        cval = clause['value']
        fval = field_value

        if isinstance(cval, list):
            tval = []
            for cv in cval:
                tval.append(uni_fold(cv))
            cval = tval
        else:
            cval = uni_fold(cval)

        if isinstance(fval, list):
            tval = []
            for fv in fval:
                tval.append(uni_fold(fv))
            fval = tval
        else:
            fval = uni_fold(fval)

        if clause['operator'] == 'one_of':
            if isinstance(fval, list):
                # Test whether a query value appears in a list of field values.
                return cval in fval
            else:
                # Test whether a field value appears in a list of candidates.
                return fval in cval
        else:
            return fval == cval

    def include_any(self, target):
        for clause in self.filter['clauses']:
            if self.evaluate_clause(clause, target):
                return True
        return False

    def match(self, target, action=None):
        if len(self.filter['clauses']) > 0:
            return self.include_any(target)
        else:
            return True


def uni_fold(text):
    # Convert bytes to text
    if isinstance(text, bytes):
        text = text_type(text, "utf-8")

    # Do not touch other types
    if not isinstance(text, text_type):
        return text

    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    return "".join([c for c in text if not unicodedata.combining(c)])
