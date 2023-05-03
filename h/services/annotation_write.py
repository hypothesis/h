from datetime import datetime

from sqlalchemy.orm import Session

from h import i18n
from h.models import Annotation
from h.models.document import update_document_metadata
from h.schemas import ValidationError
from h.security import Permission
from h.services.annotation_read import AnnotationReadService
from h.services.search_index import SearchIndexService
from h.traversal.group import GroupContext
from h.util.group_scope import url_in_scope

_ = i18n.TranslationStringFactory(__package__)


class AnnotationWriteService:
    """A service for storing and retrieving annotations."""

    def __init__(
        self,
        db_session: Session,
        has_permission: callable,
        search_index_service: SearchIndexService,
        annotation_read_service: AnnotationReadService,
    ):
        self._db = db_session
        self._has_permission = has_permission
        self._search_index_service = search_index_service
        self._annotation_read_service = annotation_read_service

    def create_annotation(self, data: dict) -> Annotation:
        """
        Create an annotation from already-validated data.

        :param data: Annotation data that has already been validated by
            `h.schemas.annotation.CreateAnnotationSchema`
        """

        # Set the group to be the same as the root annotation
        if references := data["references"]:
            if root_annotation := self._annotation_read_service.get_annotation_by_id(
                references[0]
            ):
                data["groupid"] = root_annotation.groupid
            else:
                raise ValidationError(
                    "references.0: "
                    + _("Annotation {id} does not exist").format(id=references[0])
                )

        document_data = data.pop("document", {})
        annotation = Annotation(**data)

        # Enable relationship loading, so we can access
        # the group, even though we've not added this to the session yet
        self._db.enable_relationship_loading(annotation)
        self._validate_group(annotation)

        annotation.created = annotation.updated = datetime.utcnow()
        annotation.document = update_document_metadata(
            self._db,
            annotation.target_uri,
            document_data["document_meta_dicts"],
            document_data["document_uri_dicts"],
            created=annotation.created,
            updated=annotation.updated,
        )

        self._db.add(annotation)
        self._db.flush()

        self._search_index_service._queue.add_by_id(  # pylint: disable=protected-access
            annotation.id, tag="storage.create_annotation", schedule_in=60
        )

        return annotation

    def _validate_group(self, annotation: Annotation):
        group = annotation.group
        if not group:
            raise ValidationError(
                "group: " + _(f"Invalid group id {annotation.groupid}")
            )

        # The user must have permission to create an annotation in the group
        # they've asked to create one in.
        if not self._has_permission(
            Permission.Group.WRITE, context=GroupContext(annotation.group)
        ):
            raise ValidationError(
                "group: " + _("You may not create annotations in the specified group!")
            )

        # If no scopes are present, or if the group is configured to allow
        # annotations outside its scope, there's nothing to do here
        if not group.scopes or not group.enforce_scope:
            return

        # The target URI must match at least one
        # of a group's defined scopes, if the group has any
        if not url_in_scope(
            annotation.target_uri, [scope.scope for scope in group.scopes]
        ):
            raise ValidationError(
                "group scope: "
                + _("Annotations for this target URI are not allowed in this group")
            )


def service_factory(_context, request) -> AnnotationWriteService:
    """Get an annotation service instance."""

    return AnnotationWriteService(
        db_session=request.db,
        has_permission=request.has_permission,
        search_index_service=request.find_service(name="search_index"),
        annotation_read_service=request.find_service(AnnotationReadService),
    )
