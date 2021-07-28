from copy import deepcopy

from pyramid import security
from pyramid.security import principals_allowed_by_permission

from h.presenters.annotation_base import AnnotationBasePresenter
from h.presenters.document_json import DocumentJSONPresenter
from h.security.permissions import Permission


class AnnotationJSONPresenter(AnnotationBasePresenter):
    """Present an annotation in the JSON format returned by API requests."""

    def __init__(self, annotation_context, formatters=None):
        super().__init__(annotation_context)

        self._formatters = tuple(formatters or [])

    def asdict(self):
        annotation = deepcopy(self.annotation.extra) or {}

        annotation.update(
            {
                "id": self.annotation.id,
                "created": self.created,
                "updated": self.updated,
                "user": self.annotation.userid,
                "uri": self.annotation.target_uri,
                "text": self.text,
                "tags": self.tags,
                "group": self.annotation.groupid,
                #  Convert our simple internal annotation storage format into the
                #  legacy complex permissions dict format that is still used in
                #  some places.
                "permissions": {
                    "read": [self._get_read_permission()],
                    "admin": [self.annotation.userid],
                    "update": [self.annotation.userid],
                    "delete": [self.annotation.userid],
                },
                "target": self.target,
                "document": DocumentJSONPresenter(self.annotation.document).asdict(),
                "links": self.links,
            }
        )

        if self.annotation.references:
            annotation["references"] = self.annotation.references

        for formatter in self._formatters:
            annotation.update(formatter.format(self.annotation_context))

        return annotation

    def _get_read_permission(self):
        if not self.annotation.shared:
            # It's not shared so only the owner can read it
            return self.annotation.userid

        if security.Everyone in principals_allowed_by_permission(
            self.annotation_context, Permission.Annotation.READ
        ):
            # Anyone in the world can read this
            return "group:__world__"

        # Only people in the group can read it
        return "group:{}".format(self.annotation.groupid)
