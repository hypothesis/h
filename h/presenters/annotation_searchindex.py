from h.presenters.document_searchindex import DocumentSearchIndexPresenter
from h.util.datetime import utc_iso8601
from h.util.user import split_user


class AnnotationSearchIndexPresenter:
    """Present an annotation in the JSON format used in the search index."""

    def __init__(self, annotation, request):
        self.annotation = annotation
        self.request = request

    def asdict(self):
        docpresenter = DocumentSearchIndexPresenter(self.annotation.document)
        userid_parts = split_user(self.annotation.userid)

        tags = self.annotation.tags or []

        result = {
            "authority": userid_parts["domain"],
            "id": self.annotation.id,
            "created": utc_iso8601(self.annotation.created),
            "updated": utc_iso8601(self.annotation.updated),
            "user": self.annotation.userid,
            "user_raw": self.annotation.userid,
            "uri": self.annotation.target_uri,
            "text": self.annotation.text or "",
            "tags": tags,
            "tags_raw": tags,
            "group": self.annotation.groupid,
            "shared": self.annotation.shared,
            "target": self.annotation.target,
            "document": docpresenter.asdict(),
            "thread_ids": self.annotation.thread_ids,
        }

        result["target"][0]["scope"] = [self.annotation.target_uri_normalized]

        if self.annotation.references:
            result["references"] = self.annotation.references

        self._add_hidden(result)
        self._add_nipsa(result, self.annotation.userid)

        return result

    def _add_hidden(self, result):
        # Mark an annotation as hidden if it and all of it's children have been
        # moderated and hidden.
        parents_and_replies = [self.annotation.id] + self.annotation.thread_ids

        ann_mod_svc = self.request.find_service(name="annotation_moderation")
        is_hidden = len(ann_mod_svc.all_hidden(parents_and_replies)) == len(
            parents_and_replies
        )

        result["hidden"] = is_hidden

    def _add_nipsa(self, result, user_id):
        nipsa_service = self.request.find_service(name="nipsa")
        if nipsa_service.is_flagged(user_id):
            result["nipsa"] = True
