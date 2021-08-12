from sqlalchemy.orm import subqueryload

from h import storage
from h.models import Annotation
from h.presenters import AnnotationJSONPresenter
from h.security.permissions import Permission
from h.services.annotation_json_presentation import _formatters
from h.traversal import AnnotationContext


class AnnotationJSONPresentationService:
    def __init__(self, session, user, links_svc, flag_svc, user_svc, has_permission):
        self.user = user
        self.session = session
        self.links_svc = links_svc
        self.flag_svc = flag_svc
        self.user_svc = user_svc
        self._has_permission = has_permission

        self.formatters = [_formatters.HiddenFormatter(has_permission, user)]

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

        if self._current_user_is_moderator(annotation):
            model["moderation"] = {"flagCount": self.flag_svc.flag_count(annotation)}

        # This is a dumb relic of when there was more than one, and it will
        # be gone soon, but this minimises the churn in the tests for now
        for formatter in self.formatters:
            model.update(formatter.format(annotation))

        return model

    def _current_user_is_moderator(self, annotation):
        return self._has_permission(
            Permission.Annotation.MODERATE, context=AnnotationContext(annotation)
        )

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

        # This primes the cache for `flagged()` and `flag_count()`
        self.flag_svc.all_flagged(user, annotation_ids)
        self.flag_svc.flag_counts(annotation_ids)

        # Optimise the user service `fetch()` call in the AnnotationJSONPresenter
        self.user_svc.fetch_all([annotation.userid for annotation in annotations])

        return annotations
