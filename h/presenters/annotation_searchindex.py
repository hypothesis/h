from h.presenters.annotation_base import AnnotationBasePresenter
from h.presenters.document_searchindex import DocumentSearchIndexPresenter
from h.util.user import split_user


class AnnotationSearchIndexPresenter:
    """Present an annotation in the JSON format used in the search index."""

    def __init__(self, annotation, request):
        self.annotation = annotation
        self.request = request

    def asdict(self):
        annotation = self.annotation

        tags = AnnotationBasePresenter.tags(annotation)

        result = {
            "authority": split_user(annotation.userid)["domain"],
            "id": annotation.id,
            "created": AnnotationBasePresenter.created(annotation),
            "updated": AnnotationBasePresenter.updated(annotation),
            "user": annotation.userid,
            "user_raw": annotation.userid,
            "uri": annotation.target_uri,
            "text": AnnotationBasePresenter.text(annotation),
            "tags": tags,
            "tags_raw": tags,
            "group": annotation.groupid,
            "shared": annotation.shared,
            "target": AnnotationBasePresenter.target(annotation),
            "document": DocumentSearchIndexPresenter(annotation.document).asdict(),
            "thread_ids": annotation.thread_ids,
        }

        result["target"][0]["scope"] = [annotation.target_uri_normalized]

        if annotation.references:
            result["references"] = annotation.references

        result["hidden"] = self._is_hidden(annotation)

        if self.request.find_service(name="nipsa").is_flagged(annotation.userid):
            result["nipsa"] = True

        return result

    def _is_hidden(self, annotation):
        # Mark an annotation as hidden if it and all of it's children have been
        # moderated and hidden.
        parents_and_replies = [annotation.id] + annotation.thread_ids

        ann_mod_svc = self.request.find_service(name="annotation_moderation")
        return len(ann_mod_svc.all_hidden(parents_and_replies)) == len(
            parents_and_replies
        )

