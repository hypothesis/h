from sqlalchemy.orm import subqueryload

from h import formatters, storage
from h.models import Annotation
from h.presenters import AnnotationJSONPresenter


class AnnotationJSONPresentationService:
    def __init__(
        self,
        session,
        user,
        links_svc,
        flag_svc,
        flag_count_svc,
        moderation_svc,
        user_svc,
        has_permission,
    ):
        self.session = session
        self.links_svc = links_svc

        self.formatters = [
            formatters.AnnotationFlagFormatter(flag_svc, user),
            formatters.AnnotationHiddenFormatter(moderation_svc, has_permission, user),
            formatters.AnnotationModerationFormatter(
                flag_count_svc, user, has_permission
            ),
            formatters.AnnotationUserInfoFormatter(self.session, user_svc),
        ]

    def present(self, annotation):
        return AnnotationJSONPresenter(
            annotation, links_service=self.links_svc, formatters=self.formatters
        ).asdict()

    def present_all(self, annotation_ids):
        def eager_load_documents(query):
            return query.options(subqueryload(Annotation.document))

        annotations = storage.fetch_ordered_annotations(
            self.session, annotation_ids, query_processor=eager_load_documents
        )

        # preload formatters, so they can optimize database access
        for formatter in self.formatters:
            formatter.preload(annotation_ids)

        return [self.present(annotation) for annotation in annotations]
