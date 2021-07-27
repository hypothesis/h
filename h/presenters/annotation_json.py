import copy

from pyramid import security
from pyramid.security import principals_allowed_by_permission

from h.presenters.annotation_base import AnnotationBasePresenter
from h.presenters.document_json import DocumentJSONPresenter
from h.security.permissions import Permission


class AnnotationJSONPresenter(AnnotationBasePresenter):

    """Present an annotation in the JSON format returned by API requests."""

    def __init__(self, annotation_context, formatters=None):
        super().__init__(annotation_context)

        self._formatters = []

        if formatters is not None:
            self._formatters.extend(formatters)

    def asdict(self):
        docpresenter = DocumentJSONPresenter(self.annotation.document)

        base = {
            "id": self.annotation.id,
            "created": self.created,
            "updated": self.updated,
            "user": self.annotation.userid,
            "uri": self.annotation.target_uri,
            "text": self.text,
            "tags": self.tags,
            "group": self.annotation.groupid,
            "permissions": self.permissions,
            "target": self.target,
            "document": docpresenter.asdict(),
            "links": self.links,
        }

        if self.annotation.references:
            base["references"] = self.annotation.references

        annotation = copy.copy(self.annotation.extra) or {}
        annotation.update(base)

        for formatter in self._formatters:
            annotation.update(formatter.format(self.annotation_context))

        return annotation

    @property
    def permissions(self):
        """
        Return a permissions dict for the given annotation.

        Converts our simple internal annotation storage format into the legacy
        complex permissions dict format that is still used in some places.

        """
        read = self.annotation.userid
        if self.annotation.shared:
            read = "group:{}".format(self.annotation.groupid)

            principals = principals_allowed_by_permission(
                self.annotation_context, Permission.Annotation.READ
            )
            if security.Everyone in principals:
                read = "group:__world__"

        return {
            "read": [read],
            "admin": [self.annotation.userid],
            "update": [self.annotation.userid],
            "delete": [self.annotation.userid],
        }
