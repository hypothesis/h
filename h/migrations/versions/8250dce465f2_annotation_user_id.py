"""Add user_id to the annotation table."""

import sqlalchemy as sa
from alembic import op

revision = "8250dce465f2"
down_revision = "f064c2b2e04a"


def upgrade():
    op.add_column("annotation", sa.Column("user_id", sa.Integer(), nullable=True))
    # CONCURRENTLY can't be used inside a transaction. Finish the current one.
    op.execute("COMMIT")
    op.execute(
        """CREATE INDEX CONCURRENTLY ix__annotation_user_id ON annotation (user_id);"""
    )
    # See https://www.postgresql.org/docs/11/sql-altertable.html for `NOT VALID`:
    # if the NOT VALID option is used, this potentially-lengthy scan is skipped.
    # The constraint will still be enforced against subsequent inserts or updates
    # (that is, they'll fail unless there is a matching row in the referenced table,
    # in the case of foreign keys, or they'll fail unless the new row matches the specified check condition).
    # But the database will not assume that the constraint holds for all rows in the table, until it is validated by using the VALIDATE CONSTRAINT option
    op.execute(
        """ALTER TABLE annotation ADD CONSTRAINT fk__annotation__user_id__user FOREIGN KEY (user_id) REFERENCES "user" (id) NOT VALID;"""
    )


def downgrade():
    op.drop_constraint(
        op.f("fk__annotation__user_id__user"), "annotation", type_="foreignkey"
    )
    op.drop_index(op.f("ix__annotation_user_id"), table_name="annotation")
    op.drop_column("annotation", "user_id")
