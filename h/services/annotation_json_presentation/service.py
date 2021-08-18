from sqlalchemy.orm import subqueryload

from h import storage
from h.models import Annotation
from h.presenters import AnnotationJSONPresenter
from h.security.permissions import Permission
from h.traversal import AnnotationContext


class AnnotationJSONPresentationService:
    def __init__(  # pylint: disable=too-many-arguments
        self, session, user, links_svc, flag_svc, user_svc, has_permission
    ):

        self.user = user
        self.session = session
        self.links_svc = links_svc
        self.flag_svc = flag_svc
        self.user_svc = user_svc
        self._has_permission = has_permission

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
        # The flagged value depends on whether this particular user has flagged
        model = {"flagged": self.flag_svc.flagged(user=user, annotation=annotation)}

        # Only moderators see the full flag count
        user_is_moderator = self._current_user_is_moderator(annotation)
        if user_is_moderator:
            model["moderation"] = {"flagCount": self.flag_svc.flag_count(annotation)}

        # The hidden value depends on whether you are the author
        if not annotation.is_hidden or self._current_user_is_author(annotation):
            model["hidden"] = False
        else:
            model["hidden"] = True

            # Non moderators have bad content hidden from them
            if not user_is_moderator:
                model.update({"text": "", "tags": []})

        return model

    def _current_user_is_moderator(self, annotation):
        return self._has_permission(
            Permission.Annotation.MODERATE,
            context=AnnotationContext(annotation, annotation.group),
        )

    def _current_user_is_author(self, annotation):
        return self.user and self.user.userid == annotation.userid

    def _preload_data(self, user, annotation_ids):
        def eager_load_related_items(query):
            # Ensure that accessing `annotation.document` or `.moderation`
            # doesn't trigger any more queries by pre-loading these

            return query.options(
                # Optimise access to the document which is called in
                # `AnnotationJSONPresenter`
                subqueryload(Annotation.document),
                # Optimise the check used for "hidden" above
                subqueryload(Annotation.moderation),
                # Optimise the permissions check for MODERATE permissions,
                # which ultimately depends on group permissions, causing a
                # group lookup for every annotation without this
                subqueryload(Annotation.group),
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
