from copy import deepcopy

from pyramid.request import Request

from h.models import Annotation, ModerationStatus, User
from h.presenters import DocumentJSONPresenter
from h.presenters.mention_json import MentionJSONPresenter
from h.security import Identity, identity_permits
from h.security.permissions import Permission
from h.services import MentionService
from h.services.annotation_read import AnnotationReadService
from h.services.flag import FlagService
from h.services.links import LinksService
from h.services.user import UserService
from h.session import user_info
from h.traversal import AnnotationContext
from h.util.datetime import utc_iso8601


class AnnotationJSONService:
    """A service for generating API compatible JSON for annotations."""

    def __init__(  # noqa: PLR0913
        self,
        annotation_read_service: AnnotationReadService,
        links_service: LinksService,
        flag_service: FlagService,
        user_service: UserService,
        mention_service: MentionService,
        request: Request,
    ):
        """
        Instantiate the service.

        :param annotation_read_service: AnnotationReadService instance
        :param links_service: LinksService instance
        :param flag_service: FlagService instance
        :param user_service: UserService instance
        :param mention_service: MentionService instance
        :param request: The current request
        """
        self._annotation_read_service = annotation_read_service
        self._links_service = links_service
        self._flag_service = flag_service
        self._user_service = user_service
        self._mention_service = mention_service
        self._request = request

    def present(self, annotation: Annotation, with_metadata: bool = False):  # noqa: FBT002, FBT001
        """
        Get the JSON presentation of an annotation.

        This representation does not contain any user specific information and
        has only the data applicable to all users. This does not blank content
        for moderated annotations.

        :param annotation: Annotation to present
        :return: A dict suitable for JSON serialisation
        """
        model: dict = deepcopy(annotation.extra) or {}

        model.update(
            {
                "id": annotation.id,
                "created": utc_iso8601(annotation.created),
                "updated": utc_iso8601(annotation.updated),
                "user": annotation.userid,
                "uri": annotation.target_uri,
                "text": annotation.text or "",
                "tags": annotation.tags or [],
                "group": annotation.groupid,
                "moderation_status": self._get_moderation_status(annotation),
                #  Convert our simple internal annotation storage format into the
                #  legacy complex permissions dict format that is still used in
                #  some places.
                "permissions": {
                    "read": [self._get_read_permission(annotation)],
                    "admin": [annotation.userid],
                    "update": [annotation.userid],
                    "delete": [annotation.userid],
                },
                "target": annotation.target,
                "document": DocumentJSONPresenter(annotation.document).asdict(),
                "links": self._links_service.get_all(annotation),
            }
        )

        user = self._user_service.fetch(annotation.userid)
        model["mentions"] = [
            MentionJSONPresenter(mention, self._request).asdict()
            for mention in annotation.mentions
        ]
        model.update(user_info(user))

        if annotation.references:
            model["references"] = annotation.references

        if with_metadata and annotation.slim.meta:
            model["metadata"] = annotation.slim.meta.data

        return model

    def present_for_user(
        self,
        annotation: Annotation,
        user: User,
        with_metadata: bool = False,  # noqa: FBT002, FBT001
    ):
        """
        Get the JSON presentation of an annotation for a particular user.

        This representation includes extra data the specific user is privy to
        and also hides moderated content from users who should not see it.

        :param annotation: Annotation to present
        :param user: User that the annotation is being presented to
        :return: A dict suitable for JSON serialisation
        """

        # Get the basic version which isn't user specific
        model = self.present(annotation, with_metadata=with_metadata)

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

        annotations = self._annotation_read_service.get_annotations_by_id(
            ids=annotation_ids,
            eager_load=[
                # Optimise access to the document
                Annotation.document,
                # Optimise the permissions check for MODERATE permissions,
                # which ultimately depends on group permissions, causing a
                # group lookup for every annotation without this
                Annotation.group,
                # Optimise access to the mentions
                Annotation.mentions,
            ],
        )

        # Optimise the user service `fetch()` call
        self._user_service.fetch_all([annotation.userid for annotation in annotations])

        return [self.present_for_user(annotation, user) for annotation in annotations]

    @classmethod
    def _get_read_permission(cls, annotation):
        if not annotation.shared:
            # It's not shared so only the owner can read it
            return annotation.userid

        # If the annotation's group is the public group, or an unauthorized person could
        # read the annotation, then the annotation is world readable.
        if annotation.groupid == "__world__" or identity_permits(
            identity=None,
            context=AnnotationContext(annotation),
            permission=Permission.Annotation.READ,
        ):
            return "group:__world__"

        # Only people in the group can read it
        return f"group:{annotation.groupid}"

    @staticmethod
    def _get_moderation_status(annotation) -> str | None:
        if not annotation.moderation_status:
            if not annotation.shared:
                # If an annotation is private and doesn't have a moderation status, return None.
                return None

            # Otherwise it means that the moderation status hasn't been migrated yet to "APPROVED"
            return ModerationStatus.APPROVED.value

        return annotation.moderation_status.value


def factory(_context, request):
    return AnnotationJSONService(
        annotation_read_service=request.find_service(AnnotationReadService),
        links_service=request.find_service(name="links"),
        flag_service=request.find_service(name="flag"),
        user_service=request.find_service(name="user"),
        mention_service=request.find_service(MentionService),
        request=request,
    )
