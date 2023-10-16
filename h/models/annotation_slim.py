import datetime

import sqlalchemy as sa

from h.db import Base, types


class AnnotationSlim(Base):
    """
    AnnotationSlim represents fundamental properties of annotations.

    It doesn't include the annotation text, selector and extra fields.
    It does however have FK to "User", "Group" that the main table doesn't have.

    Until this table is completely fill up with a row for each row in Annotation
    we'll have duplicated information and most of the code base will read from
    "Annotation" but write to both "Annotation" and "AnnotationSlim".
    """

    __tablename__ = "annotation_slim"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    """PK on this table"""

    pubid = sa.Column(
        types.URLSafeUUID,
        sa.ForeignKey("annotation.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    """The value of annotation.id, named here pubid following the convention of group.pubid"""

    annotation = sa.orm.relationship(
        "Annotation", backref=sa.orm.backref("slim", uselist=False)
    )

    created = sa.Column(
        sa.DateTime,
        default=datetime.datetime.utcnow,
        server_default=sa.func.now(),
        nullable=False,
        index=True,
    )

    updated = sa.Column(
        sa.DateTime,
        server_default=sa.func.now(),
        default=datetime.datetime.utcnow,
        nullable=False,
        index=True,
    )

    deleted = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.sql.expression.false(),
    )

    moderated = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.sql.expression.false(),
    )

    shared = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        server_default=sa.sql.expression.false(),
    )

    document_id = sa.Column(
        sa.Integer, sa.ForeignKey("document.id", ondelete="CASCADE"), nullable=False
    )
    document = sa.orm.relationship("Document")

    user_id = sa.Column(
        sa.Integer, sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    user = sa.orm.relationship("User")

    group_id = sa.Column(
        sa.Integer, sa.ForeignKey("group.id", ondelete="CASCADE"), nullable=False
    )
    group = sa.orm.relationship("Group")
