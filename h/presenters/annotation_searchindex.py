# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.presenters.annotation_base import AnnotationBasePresenter
from h.presenters.document_searchindex import DocumentSearchIndexPresenter
from h.util.user import split_user


class AnnotationSearchIndexPresenter(AnnotationBasePresenter):

    """Present an annotation in the JSON format used in the search index."""

    def __init__(self, annotation):
        self.annotation = annotation

    def asdict(self):
        docpresenter = DocumentSearchIndexPresenter(self.annotation.document)
        userid_parts = split_user(self.annotation.userid)

        result = {
            "authority": userid_parts["domain"],
            "id": self.annotation.id,
            "created": self.created,
            "updated": self.updated,
            "user": self.annotation.userid,
            "user_raw": self.annotation.userid,
            "uri": self.annotation.target_uri,
            "text": self.text,
            "tags": self.tags,
            "tags_raw": self.tags,
            "group": self.annotation.groupid,
            "shared": self.annotation.shared,
            "target": self.target,
            "document": docpresenter.asdict(),
            "thread_ids": self.annotation.thread_ids,
        }

        result["target"][0]["scope"] = [self.annotation.target_uri_normalized]

        if self.annotation.references:
            result["references"] = self.annotation.references

        return result

    @property
    def links(self):
        # The search index presenter has no need to generate links, and so the
        # `links_service` parameter has been removed from the constructor.
        raise NotImplementedError("search index presenter doesn't have links")
