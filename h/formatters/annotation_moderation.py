from h.security.permissions import Permission
from h.traversal import AnnotationContext


class AnnotationModerationFormatter:
    """
    Formatter for exposing an annotation's moderation information.

    If the passed-in user has permission to hide the annotation (if they are a
    moderator of the annotation's group, for instance), this formatter will
    add a `moderation` key to the payload, with a count of how many users have
    flagged the annotation.
    """

    def __init__(self, flag_svc, user, has_permission):
        self._flag_svc = flag_svc
        self._user = user
        self._has_permission = has_permission

        # Local cache of flag counts. We don't need to care about detached
        # instances because we only store the annotation id and a count.
        self._cache = {}

    def preload(self, annotation_ids):
        if self._user is None:
            return None

        if not annotation_ids:
            return None

        flag_counts = self._flag_svc.flag_counts(annotation_ids)
        self._cache.update(flag_counts)
        return flag_counts

    def format(self, annotation):
        if not self._has_permission(
            Permission.Annotation.MODERATE, context=AnnotationContext(annotation)
        ):
            return {}

        flag_count = self._load(annotation)
        return {"moderation": {"flagCount": flag_count}}

    def _load(self, annotation):
        id_ = annotation.id

        if id_ in self._cache:
            return self._cache[id_]

        flag_count = self._flag_svc.flag_count(annotation)
        self._cache[id_] = flag_count
        return flag_count
