from enum import Enum


def predicate(requires=None):
    def decorator(function):
        function.requires = requires or []
        return function

    return decorator


class PredicateBasedPermissions:
    def __init__(self, mapping):
        self.mapping = self._expand_clauses(mapping)

    def permits(self, identity, context, permission):
        if clauses := self.mapping.get(permission):
            statement_cache = {}

            for clause in clauses:
                if self._clause_true(clause, statement_cache, identity, context):
                    return True

            return False

        return False

    def _clause_true(self, clause, statement_cache, identity, context):
        for predicate in clause:
            value = statement_cache.get(predicate)
            if value is None:
                if isinstance(predicate, Enum):
                    # We are going to assume this predicate is a permission
                    value = self.permits(identity, context, predicate)
                else:
                    value = predicate(identity, context)

                statement_cache[predicate] = value

            if not value:
                return False

        return True

    @classmethod
    def _expand_clauses(cls, mapping):
        return {
            permission: [list(cls._expand_clause(clause)) for clause in clauses]
            for permission, clauses in mapping.items()
        }

    @classmethod
    def _expand_clause(cls, clause):
        seen_before = set()
        for predicate in clause:
            for parent in cls._expand_predicate(predicate):
                if parent in seen_before:
                    continue

                seen_before.add(parent)
                yield parent

    @classmethod
    def _expand_predicate(cls, predicate):
        if hasattr(predicate, "requires"):
            for parent in predicate.requires:
                yield from cls._expand_predicate(parent)

        yield predicate
