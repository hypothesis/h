from h.security.permissions import Permission
from h.traversal import AnnotationContext


class HiddenFormatter:
    """
    Formatter for dealing with annotations that a moderator has hidden.

    Any user who has permission to moderate a group will always be able to see
    whether annotations in a group have been hidden, and will be able to see
    the content of those annotations. In the unlikely event that these
    annotations are their own, they'll still be able to see them.

    Moderators aside, users are never shown that their own annotations have
    been hidden. They are always given a `False` value for the `hidden` flag.

    For any other users, if an annotation has been hidden it is presented with
    the `hidden` flag set to `True`, and the annotation's content is redacted.
    """

    def __init__(self, has_permission, user):
        self._has_permission = has_permission
        self._user = user

    def preload(self, annotation_ids):
        """Preload annotation ids."""

        # We don't do anything here but must meet the expected interface

    def format(self, annotation):
        if not annotation.is_hidden or self._current_user_is_author(annotation):
            return {"hidden": False}

        result = {"hidden": True}

        if not self._current_user_is_moderator(annotation):
            result.update({"text": "", "tags": []})

        return result

    def _current_user_is_moderator(self, annotation):
        return self._has_permission(
            Permission.Annotation.MODERATE, context=AnnotationContext(annotation)
        )

    def _current_user_is_author(self, annotation):
        return self._user and self._user.userid == annotation.userid
