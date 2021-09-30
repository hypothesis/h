from copy import deepcopy

from h.presenters.document_json import DocumentJSONPresenter
from h.security import Permission, identity_permits
from h.session import user_info
from h.traversal import AnnotationContext
from h.util.datetime import utc_iso8601


class BasicJSONPresenter:
    """Present an annotation in JSON without reference to the user."""

    def __init__(self, links_service, user_service):
        self._links_service = links_service
        self._user_service = user_service

    def present(self, annotation):
        model = deepcopy(annotation.extra) or {}

        model.update(
            {
                "id": annotation.id,
                "created": utc_iso8601(annotation.created),
                "updated": utc_iso8601(annotation.updated),
                "user": annotation.userid,
                "uri": annotation.target_uri,
                "text": annotation.text or "",
                "tags": annotation.tags or [],
                "group": annotation.groupid,
                #  Convert our simple internal annotation storage format into the
                #  legacy complex permissions dict format that is still used in
                #  some places.
                "permissions": {
                    "read": [self._get_read_permission(annotation)],
                    "admin": [annotation.userid],
                    "update": [annotation.userid],
                    "delete": [annotation.userid],
                },
                "target": annotation.target,
                "document": DocumentJSONPresenter(annotation.document).asdict(),
                "links": self._links_service.get_all(annotation),
            }
        )

        model.update(user_info(self._user_service.fetch(annotation.userid)))

        if annotation.references:
            model["references"] = annotation.references

        return model

    @classmethod
    def _get_read_permission(cls, annotation):
        if not annotation.shared:
            # It's not shared so only the owner can read it
            return annotation.userid

        # If the annotation's group is the public group, or an unauthorized person could
        # read the annotation, then the annotation is world readable.
        if annotation.groupid == "__world__" or identity_permits(
            identity=None,
            context=AnnotationContext(annotation),
            permission=Permission.Annotation.READ,
        ):
            return "group:__world__"

        # Only people in the group can read it
        return f"group:{annotation.groupid}"
