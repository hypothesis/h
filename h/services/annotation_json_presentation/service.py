from sqlalchemy.orm import subqueryload

from h import formatters, storage
from h.models import Annotation
from h.presenters import AnnotationJSONPresenter


class AnnotationJSONPresentationService:
    def __init__(self, session, user, links_svc, flag_svc, has_permission):
        self.session = session
        self.links_svc = links_svc

        self.formatters = [
            formatters.AnnotationFlagFormatter(flag_svc, user),
            formatters.AnnotationHiddenFormatter(has_permission, user),
            formatters.AnnotationModerationFormatter(flag_svc, user, has_permission),
            formatters.AnnotationUserInfoFormatter(),
        ]

    def present(self, annotation):
        return AnnotationJSONPresenter(
            annotation, links_service=self.links_svc, formatters=self.formatters
        ).asdict()

    def present_all(self, annotation_ids):
        def eager_load_related_items(query):
            return query.options(
                # Ensure that accessing `annotation.document` or `.moderation`
                # etc. doesn't trigger any more queries by pre-loading these
                subqueryload(Annotation.document),
                subqueryload(Annotation.moderation),
                subqueryload(Annotation.user),
            )

        annotations = storage.fetch_ordered_annotations(
            self.session, annotation_ids, query_processor=eager_load_related_items
        )

        # preload formatters, so they can optimize database access
        for formatter in self.formatters:
            formatter.preload(annotation_ids)

        return [self.present(annotation) for annotation in annotations]
