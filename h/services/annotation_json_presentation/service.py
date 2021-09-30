from sqlalchemy.orm import subqueryload

from h import storage
from h.models import Annotation, User
from h.security import Identity, identity_permits
from h.security.permissions import Permission
from h.services.annotation_json_presentation._basic_presenter import BasicJSONPresenter
from h.traversal import AnnotationContext


class AnnotationJSONPresentationService:
    """A service for generating API compatible JSON for annotations."""

    def __init__(self, session, links_service, flag_service, user_service):
        """
        Instantiate the service.

        :param session: DB session
        :param links_service: LinksService instance
        :param flag_service: FlagService instance
        :param user_service: UserService instance
        """
        self._session = session
        self._links_service = links_service
        self._flag_service = flag_service
        self._user_service = user_service

        self._presenter = BasicJSONPresenter(
            links_service=links_service, user_service=user_service
        )

    def present(self, annotation: Annotation):
        """
        Get the JSON presentation of an annotation.

        This representation does not contain any user specific information and
        has only the data applicable to all users. This does not blank content
        for moderated annotations.

        :param annotation: Annotation to present
        :return: A dict suitable for JSON serialisation
        """
        return self._presenter.present(annotation)

    def present_for_user(self, annotation: Annotation, user: User):
        """
        Get the JSON presentation of an annotation for a particular user.

        This representation includes extra data the specific user is privy to
        and also hides moderated content from users who should not see it.

        :param annotation: Annotation to present
        :param user: User that the annotation is being presented to
        :return: A dict suitable for JSON serialisation
        """

        # Get the basic version which isn't user specific
        model = self.present(annotation)

        # The flagged value depends on whether this particular user has flagged
        model["flagged"] = self._flag_service.flagged(user=user, annotation=annotation)

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
        user_is_author = user and user.userid == annotation.userid
        if user_is_author or not annotation.is_hidden:
            model["hidden"] = False
        else:
            model["hidden"] = True

            # Non moderators have bad content hidden from them
            if not user_is_moderator:
                model.update({"text": "", "tags": []})

        return model

    def present_all_for_user(self, annotation_ids, user: User):
        """
        Get the JSON presentation of many annotations for a particular user.

        This method is more efficient than repeatedly calling
        `present_for_user` when generating a large number of annotations for
        the same user, but returns the same information (but in a list).

        :param annotation_ids: Annotation to present
        :param user: User that the annotation is being presented to
        :return: A list of dicts suitable for JSON serialisation.
        """

        # This primes the cache for `flagged()` and `flag_count()`
        self._flag_service.all_flagged(user, annotation_ids)
        self._flag_service.flag_counts(annotation_ids)

        annotations = storage.fetch_ordered_annotations(
            self._session,
            annotation_ids,
            query_processor=self._eager_load_related_items,
        )

        # Optimise the user service `fetch()` call
        self._user_service.fetch_all([annotation.userid for annotation in annotations])

        return [self.present_for_user(annotation, user) for annotation in annotations]

    @staticmethod
    def _eager_load_related_items(query):
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
