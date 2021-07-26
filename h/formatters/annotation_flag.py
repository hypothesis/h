class AnnotationFlagFormatter:
    """
    Formatter for exposing a user's annotation flags.

    If the passed-in user has flagged an annotation, this formatter will
    add: `"flagged": true` to the payload, otherwise `"flagged": false`.
    """

    def __init__(self, flag_service, user=None):
        self.flag_service = flag_service
        self.user = user

        # Local cache of flags. We don't need to care about detached
        # instances because we only store the annotation id and a boolean flag.
        self._cache = {}

    def preload(self, annotation_ids):
        if self.user is None:
            return None

        flagged_ids = self.flag_service.all_flagged(
            user=self.user, annotation_ids=annotation_ids
        )

        flags = {
            annotation_id: (annotation_id in flagged_ids)
            for annotation_id in annotation_ids
        }
        self._cache.update(flags)
        return flags

    def format(self, annotation_context):
        flagged = self._load(annotation_context.annotation)
        return {"flagged": flagged}

    def _load(self, annotation):
        if self.user is None:
            return False

        id_ = annotation.id

        if id_ in self._cache:
            return self._cache[id_]

        flagged = self.flag_service.flagged(user=self.user, annotation=annotation)
        self._cache[id_] = flagged
        return self._cache[id_]
