from sqlalchemy.orm import subqueryload

from h import storage
from h.models import Annotation
from h.presenters import AnnotationJSONPresenter
from h.services.annotation_json_presentation import _formatters


class AnnotationJSONPresentationService:
    def __init__(self, session, user, links_svc, flag_svc, user_svc, has_permission):
        self.user = user
        self.session = session
        self.links_svc = links_svc
        self.flag_svc = flag_svc
        self.user_svc = user_svc

        self.formatters = [
            _formatters.HiddenFormatter(has_permission, user),
            _formatters.ModerationFormatter(flag_svc, user, has_permission),
        ]

    def present(self, annotation):
        model = AnnotationJSONPresenter(
            annotation, links_service=self.links_svc, user_service=self.user_svc
        ).asdict()

        model.update(self._get_user_dependent_content(self.user, annotation))

        return model

    def present_all(self, annotation_ids):
        annotations = self._preload_data(self.user, annotation_ids)

        return [self.present(annotation) for annotation in annotations]

    def _get_user_dependent_content(self, user, annotation):
        model = {"flagged": self.flag_svc.flagged(user=user, annotation=annotation)}

        for formatter in self.formatters:
            model.update(formatter.format(annotation))

        return model

    def _preload_data(self, user, annotation_ids):
        def eager_load_related_items(query):
            return query.options(
                # Ensure that accessing `annotation.document` or `.moderation`
                # doesn't trigger any more queries by pre-loading these
                subqueryload(Annotation.document),
                subqueryload(Annotation.moderation),
            )

        annotations = storage.fetch_ordered_annotations(
            self.session, annotation_ids, query_processor=eager_load_related_items
        )

        # This primes the cache for `flagged()`
        self.flag_svc.all_flagged(user, annotation_ids)

        # Optimise the user service `fetch()` call in the AnnotationJSONPresenter
        self.user_svc.fetch_all([annotation.userid for annotation in annotations])

        # preload formatters, so they can optimize database access
        for formatter in self.formatters:
            formatter.preload(annotation_ids)

        return annotations
