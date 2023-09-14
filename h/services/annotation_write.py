from collections.abc import Callable
from datetime import datetime

from sqlalchemy import exists, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from h import i18n
from h.models import Annotation, AnnotationModeration, AnnotationSlim, User
from h.models.document import update_document_metadata
from h.schemas import ValidationError
from h.security import Permission
from h.services.annotation_metadata import AnnotationMetadataService
from h.services.annotation_read import AnnotationReadService
from h.services.search_index import SearchIndexService
from h.traversal.group import GroupContext
from h.util.group_scope import url_in_scope

_ = i18n.TranslationStringFactory(__package__)


class AnnotationWriteService:
    """A service for storing and retrieving annotations."""

    def __init__(  # pylint:disable=too-many-arguments
        self,
        db_session: Session,
        has_permission: Callable,
        search_index_service: SearchIndexService,
        annotation_read_service: AnnotationReadService,
        annotation_metadata_service: AnnotationMetadataService,
    ):
        self._db = db_session
        self._has_permission = has_permission
        self._search_index_service = search_index_service
        self._annotation_read_service = annotation_read_service
        self._annotation_metadata_service = annotation_metadata_service

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

        annotation_metadata = data.pop("metadata", None)
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
        self.upsert_annotation_slim(annotation)

        if annotation_metadata:
            self._annotation_metadata_service.set(annotation, annotation_metadata)

        self._search_index_service._queue.add_by_id(  # pylint: disable=protected-access
            annotation.id, tag="storage.create_annotation", schedule_in=60
        )

        return annotation

    def update_annotation(
        # pylint: disable=too-many-arguments
        self,
        annotation: Annotation,
        data: dict,
        update_timestamp: bool = True,
        reindex_tag: str = "storage.update_annotation",
        enforce_write_permission: bool = True,
    ) -> Annotation:
        """
        Update an annotation and its associated document metadata.

        :param annotation: Annotation to be updated
        :param data: Validated data with which to update the annotation
        :param update_timestamp: Whether to update the last-edited timestamp of
            the annotation.
        :param reindex_tag: Tag used by the reindexing job to identify the
            source of the reindexing request.
        :param enforce_write_permission: Check that the user has permissions
            to write to the group the annotation is in
        """
        initial_target_uri = annotation.target_uri

        annotation_metadata = data.pop("metadata", None)
        self._update_annotation_values(annotation, data)
        if update_timestamp:
            annotation.updated = datetime.utcnow()

        # Expire the group relationship, so we get the most up-to-date value
        # instead of the one which was present when we loaded the model
        # https://docs.sqlalchemy.org/en/13/faq/sessions.html#i-set-the-foo-id-attribute-on-my-instance-to-7-but-the-foo-attribute-is-still-none-shouldn-t-it-have-loaded-foo-with-id-7
        self._db.expire(annotation, ["group"])
        self._validate_group(
            annotation, enforce_write_permission=enforce_write_permission
        )

        if (
            document := data.get("document", {})
        ) or annotation.target_uri != initial_target_uri:
            annotation.document = update_document_metadata(
                self._db,
                annotation.target_uri,
                document.get("document_meta_dicts", {}),
                document.get("document_uri_dicts", {}),
                updated=annotation.updated,
            )
        self.upsert_annotation_slim(annotation)

        if annotation_metadata:
            self._annotation_metadata_service.set(annotation, annotation_metadata)

        # The search index service by default does not reindex if the existing ES
        # entry's timestamp matches the DB timestamp. If we're not changing this
        # timestamp, we need to force reindexing.
        # pylint: disable=protected-access
        self._search_index_service._queue.add_by_id(
            annotation.id,
            tag=reindex_tag,
            schedule_in=60,
            force=not update_timestamp,
        )

        return annotation

    def hide(self, annotation):
        """Hides  an annotation marking it it as "moderated"."""
        if not annotation.is_hidden:
            annotation.moderation = AnnotationModeration()

        self.upsert_annotation_slim(annotation)

    def unhide(self, annotation):
        """Remove the moderation status of an annotation."""
        annotation.moderation = None
        self.upsert_annotation_slim(annotation)

    @staticmethod
    def change_document(db, old_document_ids, new_document):
        """Update the annotations that pointed to any of `old_document_ids` to point to `new_document` instead."""
        db.query(Annotation).filter(
            Annotation.document_id.in_(old_document_ids)
        ).update({Annotation.document_id: new_document.id}, synchronize_session="fetch")
        db.query(AnnotationSlim).filter(
            AnnotationSlim.document_id.in_(old_document_ids)
        ).update(
            {AnnotationSlim.document_id: new_document.id}, synchronize_session="fetch"
        )

    @staticmethod
    def _update_annotation_values(annotation: Annotation, data: dict):
        for key, value in data.items():
            # Don't set complex things
            if key in ("document", "extra"):
                continue

            setattr(annotation, key, value)

        extra = data.get("extra", {})
        annotation.extra.update(extra)

    def _validate_group(self, annotation: Annotation, enforce_write_permission=True):
        group = annotation.group
        if not group:
            raise ValidationError(
                "group: " + _(f"Invalid group id {annotation.groupid}")
            )

        # The user must have permission to write to the group
        if enforce_write_permission and not self._has_permission(
            Permission.Group.WRITE, context=GroupContext(annotation.group)
        ):
            raise ValidationError(
                "group: " + _("You may not create annotations in the specified group!")
            )

        if (
            group.scopes  # If we have scopes
            and group.enforce_scope  # ... and we are enforcing them
            # the target URI must match one of a group's defined scopes
            and not url_in_scope(
                annotation.target_uri, [scope.scope for scope in group.scopes]
            )
        ):
            raise ValidationError(
                "group scope: "
                + _("Annotations for this target URI are not allowed in this group")
            )

    def upsert_annotation_slim(self, annotation):
        self._db.flush()  # See the last model changes in the transaction
        moderated = self._db.scalar(
            select(
                exists(
                    select(AnnotationModeration.id).where(
                        AnnotationModeration.annotation_id == annotation.id
                    )
                )
            )
        )
        user_id = self._db.scalar(
            select(User.id).where(User.userid == annotation.userid)
        )

        stmt = insert(AnnotationSlim).values(
            [
                {
                    # Index to upsert on
                    "pubid": annotation.id,
                    # Directly from the annotation
                    "created": annotation.created,
                    "updated": annotation.updated,
                    "deleted": annotation.deleted,
                    "shared": annotation.shared,
                    "document_id": annotation.document_id,
                    # Fields of AnnotationSlim
                    "group_id": annotation.group.id,
                    "user_id": user_id,
                    "moderated": moderated,
                }
            ]
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["pubid"],
            set_={
                # Fields to update
                "updated": stmt.excluded.updated,
                "deleted": stmt.excluded.deleted,
                "shared": stmt.excluded.shared,
                "document_id": stmt.excluded.document_id,
                "group_id": stmt.excluded.group_id,
                "user_id": stmt.excluded.user_id,
                "moderated": stmt.excluded.moderated,
            },
        )
        self._db.execute(stmt)


def service_factory(_context, request) -> AnnotationWriteService:
    """Get an annotation service instance."""

    return AnnotationWriteService(
        db_session=request.db,
        has_permission=request.has_permission,
        search_index_service=request.find_service(name="search_index"),
        annotation_read_service=request.find_service(AnnotationReadService),
        annotation_metadata_service=request.find_service(AnnotationMetadataService),
    )
