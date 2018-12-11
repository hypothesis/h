# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from h.presenters.annotation_base import AnnotationBasePresenter
from h.presenters.document_searchindex import DocumentSearchIndexPresenter
from h.util.user import split_user


class AnnotationSearchIndexPresenter(AnnotationBasePresenter):

    """Present an annotation in the JSON format used in the search index."""

    def __init__(self, annotation, request):
        self.annotation = annotation
        self.request = request

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

        # Mark an annotation as hidden if it and all of it's children have been
        # moderated and hidden.
        parents_and_replies = [self.annotation.id] + self.annotation.thread_ids

        ann_mod_svc = self.request.find_service(name="annotation_moderation")
        result["hidden"] = len(ann_mod_svc.all_hidden(parents_and_replies)) == len(
            parents_and_replies
        )

        return result

    @property
    def links(self):
        # The search index presenter has no need to generate links, and so the
        # `links_service` parameter has been removed from the constructor.
        raise NotImplementedError("search index presenter doesn't have links")
