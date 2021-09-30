from sqlalchemy.orm import subqueryload

from h import storage
from h.models import Annotation
from h.security import Identity, identity_permits
from h.security.permissions import Permission
from h.services.annotation_json_presentation._basic_presenter import BasicJSONPresenter
from h.traversal import AnnotationContext


class AnnotationJSONPresentationService:
    def __init__(  # pylint: disable=too-many-arguments
        self, session, links_svc, flag_svc, user_svc
    ):
        self._session = session
        self._links_service = links_svc
        self._user_service = user_svc
        self._flag_service = flag_svc
        self._presenter = BasicJSONPresenter(
            links_service=self._links_service, user_service=self._user_service
        )

    def present(self, annotation):
        return self._presenter.present(annotation)

    def present_for_user(self, annotation, user):
        model = self.present(annotation)
        model.update(self._get_user_dependent_content(annotation, user))

        return model

    def present_all_for_user(self, annotation_ids, user):
        annotations = self._preload_data(user, annotation_ids)

        return [self.present_for_user(annotation, user) for annotation in annotations]

    def _get_user_dependent_content(self, annotation, user):
        # The flagged value depends on whether this particular user has flagged
        model = {
            "flagged": self._flag_service.flagged(user=user, annotation=annotation)
        }

        # Only moderators see the full flag count
        user_is_moderator = identity_permits(
            identity=Identity.from_models(user=user),
            context=AnnotationContext(annotation),
            permission=Permission.Annotation.MODERATE,
        )
        if user_is_moderator:
            model["moderation"] = {
                "flagCount": self._flag_service.flag_count(annotation)
            }

        # The hidden value depends on whether you are the author
        if not annotation.is_hidden or self._user_is_author(user, annotation):
            model["hidden"] = False
        else:
            model["hidden"] = True

            # Non moderators have bad content hidden from them
            if not user_is_moderator:
                model.update({"text": "", "tags": []})

        return model

    @classmethod
    def _user_is_author(cls, user, annotation):
        return user and user.userid == annotation.userid

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
            self._session, annotation_ids, query_processor=eager_load_related_items
        )

        # This primes the cache for `flagged()` and `flag_count()`
        self._flag_service.all_flagged(user, annotation_ids)
        self._flag_service.flag_counts(annotation_ids)

        # Optimise the user service `fetch()` call in the AnnotationJSONPresenter
        self._user_service.fetch_all([annotation.userid for annotation in annotations])

        return annotations
