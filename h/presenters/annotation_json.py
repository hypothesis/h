from copy import deepcopy

from pyramid import security
from pyramid.security import principals_allowed_by_permission

from h.presenters.annotation_base import AnnotationBasePresenter
from h.presenters.document_json import DocumentJSONPresenter
from h.security.permissions import Permission
from h.session import user_info
from h.traversal import AnnotationContext


class AnnotationJSONPresenter(AnnotationBasePresenter):
    """Present an annotation in the JSON format returned by API requests."""

    def __init__(self, annotation, links_service):
        super().__init__(annotation)

        self._links_service = links_service

    def asdict(self):
        model = deepcopy(self.annotation.extra) or {}

        model.update(
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
                "links": self._links_service.get_all(self.annotation),
            }
        )

        model.update(user_info(self.annotation.user))

        if self.annotation.references:
            model["references"] = self.annotation.references

        return model

    def _get_read_permission(self):
        if not self.annotation.shared:
            # It's not shared so only the owner can read it
            return self.annotation.userid

        if security.Everyone in principals_allowed_by_permission(
            AnnotationContext(self.annotation), Permission.Annotation.READ
        ):
            # Anyone in the world can read this
            return "group:__world__"

        # Only people in the group can read it
        return "group:{}".format(self.annotation.groupid)
