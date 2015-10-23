"""Add constraints to pubid field

Revision ID: 43645baa68b2
Revises: 1f82507200d7
Create Date: 2015-10-23 13:16:26.408333

"""

# revision identifiers, used by Alembic.
revision = '43645baa68b2'
down_revision = '1f82507200d7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Make the column non-nullable. This is an O(1) operation.
    op.alter_column('group', 'pubid', nullable=False)

    # Add the UNIQUE constraint. We do this in a way that doesn't lock the
    # table: first, add the index concurrently. We can't do that in a
    # transaction so we commit the current one.
    op.execute('COMMIT')
    op.create_index(op.f('uq__group__pubid'), 'group', ['pubid'],
                    unique=True,
                    postgresql_concurrently=True)

    # Second, we create the constraint using the already-created index.
    op.execute(sa.text('ALTER TABLE public.group '
                       'ADD CONSTRAINT uq__group__pubid '
                       'UNIQUE USING INDEX uq__group__pubid'))


def downgrade():
    op.drop_constraint(op.f('uq__group__pubid'), 'group', type_='unique')
    op.alter_column('group', 'pubid', nullable=True)
