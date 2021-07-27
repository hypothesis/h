from sqlalchemy.orm import subqueryload

from h import formatters, models, presenters, storage, traversal
from h.security.permissions import Permission


class AnnotationJSONPresentationService:
    def __init__(
        self,
        session,
        user,
        group_svc,
        links_svc,
        flag_svc,
        flag_count_svc,
        moderation_svc,
        user_svc,
        has_permission,
    ):
        self.session = session
        self.group_svc = group_svc
        self.links_svc = links_svc

        def moderator_check(group):
            return has_permission(Permission.Group.MODERATE, group)

        self.formatters = [
            formatters.AnnotationFlagFormatter(flag_svc, user),
            formatters.AnnotationHiddenFormatter(moderation_svc, moderator_check, user),
            formatters.AnnotationModerationFormatter(
                flag_count_svc, user, has_permission
            ),
            formatters.AnnotationUserInfoFormatter(self.session, user_svc),
        ]

    def present(self, annotation_resource):
        presenter = self._get_presenter(annotation_resource)
        return presenter.asdict()

    def present_all(self, annotation_ids):
        def eager_load_documents(query):
            return query.options(subqueryload(models.Annotation.document))

        annotations = storage.fetch_ordered_annotations(
            self.session, annotation_ids, query_processor=eager_load_documents
        )

        # preload formatters, so they can optimize database access
        for formatter in self.formatters:
            formatter.preload(annotation_ids)

        return [
            self.present(
                traversal.AnnotationContext(ann, self.group_svc, self.links_svc)
            )
            for ann in annotations
        ]

    def _get_presenter(self, annotation_resource):
        return presenters.AnnotationJSONPresenter(annotation_resource, self.formatters)
