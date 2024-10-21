import logging

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.ext.hybrid import hybrid_property

from h.db import Base, mixins
from h.models.document._exceptions import ConcurrentUpdateError
from h.util.uri import normalize as uri_normalize

log = logging.getLogger(__name__)


class DocumentMeta(Base, mixins.Timestamps):
    __tablename__ = "document_meta"
    __table_args__ = (
        sa.UniqueConstraint("claimant_normalized", "type"),
        sa.Index("ix__document_meta_document_id", "document_id"),
        sa.Index("ix__document_meta_updated", "updated"),
    )

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    _claimant = sa.Column("claimant", sa.UnicodeText, nullable=False)
    _claimant_normalized = sa.Column(
        "claimant_normalized", sa.UnicodeText, nullable=False
    )

    type = sa.Column(sa.UnicodeText, nullable=False)
    value = sa.Column(pg.ARRAY(sa.UnicodeText, zero_indexes=True), nullable=False)

    document_id = sa.Column(sa.Integer, sa.ForeignKey("document.id"), nullable=False)

    @hybrid_property
    def claimant(self):
        return self._claimant

    @claimant.setter
    def claimant(self, value):
        self._claimant = value
        self._claimant_normalized = uri_normalize(value)

    @hybrid_property
    def claimant_normalized(self):
        return self._claimant_normalized

    def __repr__(self):
        return f"<DocumentMeta {self.id}>"


def create_or_update_document_meta(  # pylint:disable=redefined-builtin,too-many-arguments, too-many-positional-arguments
    session, claimant, type, value, document, created, updated
):
    """
    Create or update a DocumentMeta with the given parameters.

    If an equivalent DocumentMeta already exists in the database then its value
    and updated time will be updated otherwise a new one will be created and
    added to the database.

    To be considered "equivalent" an existing DocumentMeta must have the given
    claimant and type, but its value, document and created and updated times
    needn't match the given ones.

    :param session: the database session
    :param claimant: the value to use for the DocumentMeta's claimant attribute
        if a new DocumentMeta is created
    :param type: the value of the new or existing DocumentMeta's type attribute

    :param value: the value to set the new or existing DocumentMeta's value
        attribute to
    :type value: list of unicode strings

    :param document: the value to use for the DocumentMeta's document if a new
        DocumentMeta is created
    :type document: h.models.Document

    :param created: the value to use for the DocumentMeta's created attribute
        if a new DocumentMeta is created
    :param updated: the value to set the new or existing DocumentMeta's updated
        attribute to
    """
    existing_dm = (
        session.query(DocumentMeta)
        .filter(
            DocumentMeta.claimant_normalized == uri_normalize(claimant),
            DocumentMeta.type == type,
        )
        .one_or_none()
    )

    if existing_dm is None:
        session.add(
            DocumentMeta(
                claimant=claimant,
                type=type,
                value=value,
                document=document,
                created=created,
                updated=updated,
            )
        )
    else:
        existing_dm.value = value
        existing_dm.updated = updated
        if not existing_dm.document == document:
            log.warning(
                "Found DocumentMeta (id: %s)'s document_id (%s) doesn't "
                "match given Document's id (%s)",
                existing_dm.id,
                existing_dm.document_id,
                document.id,
            )

    if type == "title" and value and not document.title:
        document.title = value[0]

    try:
        session.flush()
    except sa.exc.IntegrityError as err:
        raise ConcurrentUpdateError("concurrent document meta updates") from err
