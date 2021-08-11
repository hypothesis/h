class FlagFormatter:
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

        for annotation_id in annotation_ids:
            self._cache[annotation_id] = annotation_id in flagged_ids

        return self._cache

    def format(self, annotation):
        return {"flagged": self._is_flagged(annotation)}

    def _is_flagged(self, annotation):
        if self.user is None:
            return False

        if annotation.id not in self._cache:
            self._cache[annotation.id] = self.flag_service.flagged(
                user=self.user, annotation=annotation
            )

        return self._cache[annotation.id]
