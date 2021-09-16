from copy import deepcopy

from pyramid import security
from pyramid.security import principals_allowed_by_permission

from h.presenters.annotation_base import AnnotationBasePresenter
from h.presenters.document_json import DocumentJSONPresenter
from h.security import Permission
from h.session import user_info
from h.traversal import AnnotationContext
from h.util.datetime import utc_iso8601


class AnnotationJSONPresenter(AnnotationBasePresenter):
    """Present an annotation in the JSON format returned by API requests."""

    def __init__(self, annotation, links_service, user_service):
        super().__init__(annotation)

        self._links_service = links_service
        self._user_service = user_service

    def asdict(self):
        annotation = deepcopy(self.annotation.extra) or {}

        annotation.update(
            {
                "id": self.annotation.id,
                "created": utc_iso8601(self.annotation.created),
                "updated": utc_iso8601(self.annotation.updated),
                "user": self.annotation.userid,
                "uri": self.annotation.target_uri,
                "text": self.annotation.text or "",
                "tags": self.annotation.tags or [],
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

        annotation.update(user_info(self._user_service.fetch(self.annotation.userid)))

        if self.annotation.references:
            annotation["references"] = self.annotation.references

        return annotation

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
