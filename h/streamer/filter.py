# -*- coding: utf-8 -*-

import copy
import operator
import unicodedata

from jsonpointer import resolve_pointer
from h._compat import text_type

SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "optional": True},
        "match_policy": {
            "type": "string",
            "enum": ["include_any", "include_all",
                     "exclude_any", "exclude_all"]
        },
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
                    "enum": ["equals", "matches", "lt", "le", "gt", "ge",
                             "one_of", "first_of", "match_of",
                             "lene", "leng", "lenge", "lenl", "lenle"]
                },
                "value": "object",
                "options": {"type": "object", "default": {}}
            }
        },
    },
    "required": ["match_policy", "clauses", "actions"]
}


class FilterHandler(object):
    def __init__(self, filter_json):
        self.filter = filter_json

    # operators
    operators = {
        'equals': 'eq',
        'matches': 'contains',
        'lt': 'lt',
        'le': 'le',
        'gt': 'gt',
        'ge': 'ge',
        'one_of': 'contains',
        'first_of': 'first_of',
        'match_of': 'match_of',
        'lene': 'lene',
        'leng': 'leng',
        'lenge': 'lenge',
        'lenl': 'lenl',
        'lenle': 'lenle',
    }

    def evaluate_clause(self, clause, target):
        if isinstance(clause['field'], list):
            for field in clause['field']:
                copied = copy.deepcopy(clause)
                copied['field'] = field
                result = self.evaluate_clause(copied, target)
                if result:
                    return True
            return False
        else:
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

            reversed_order = False
            # Determining operator order
            # Normal order: field_value, clause['value']
            # i.e. condition created > 2000.01.01
            # Here clause['value'] = '2001.01.01'.
            # The field_value is target['created']
            # So the natural order is: ge(field_value, clause['value']

            # But!
            # Reversed operator order for contains (b in a)
            if isinstance(cval, list) or isinstance(fval, list):
                if clause['operator'] in ['one_of', 'matches']:
                    reversed_order = True
                    # But not in every case. (i.e. tags matches 'b')
                    # Here field_value is a list, because an annotation can
                    # have many tags.
                    if isinstance(field_value, list):
                        reversed_order = False

            if reversed_order:
                lval = cval
                rval = fval
            else:
                lval = fval
                rval = cval

            op = getattr(operator, self.operators[clause['operator']])
            return op(lval, rval)

    # match_policies
    def include_any(self, target):
        for clause in self.filter['clauses']:
            if self.evaluate_clause(clause, target):
                return True
        return False

    def include_all(self, target):
        for clause in self.filter['clauses']:
            if not self.evaluate_clause(clause, target):
                return False
        return True

    def exclude_all(self, target):
        for clause in self.filter['clauses']:
            if not self.evaluate_clause(clause, target):
                return True
        return False

    def exclude_any(self, target):
        for clause in self.filter['clauses']:
            if self.evaluate_clause(clause, target):
                return False
        return True

    def match(self, target, action=None):
        if not action or action == 'past' or action in self.filter['actions']:
            if len(self.filter['clauses']) > 0:
                return getattr(self, self.filter['match_policy'])(target)
            else:
                return True
        else:
            return False


def first_of(a, b):
    return a[0] == b
setattr(operator, 'first_of', first_of)  # noqa:E305


def match_of(a, b):
    for subb in b:
        if subb in a:
            return True
    return False
setattr(operator, 'match_of', match_of)  # noqa:E305


def lene(a, b):
    return len(a) == b
setattr(operator, 'lene', lene)  # noqa:E305


def leng(a, b):
    return len(a) > b
setattr(operator, 'leng', leng)  # noqa:E305


def lenge(a, b):
    return len(a) >= b
setattr(operator, 'lenge', lenge)  # noqa:E305


def lenl(a, b):
    return len(a) < b
setattr(operator, 'lenl', lenl)  # noqa:E305


def lenle(a, b):
    return len(a) <= b
setattr(operator, 'lenle', lenle)  # noqa:E305


def uni_fold(text):
    # Convert bytes to text
    if isinstance(text, bytes):
        text = text_type(text, "utf-8")

    # Do not touch other types
    if not isinstance(text, text_type):
        return text

    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    return u"".join([c for c in text if not unicodedata.combining(c)])
