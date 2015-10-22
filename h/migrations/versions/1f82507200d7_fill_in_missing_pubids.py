"""Fill in missing pubids

Revision ID: 1f82507200d7
Revises: 4ed50e7ac940
Create Date: 2015-10-23 13:16:16.964214

"""

# revision identifiers, used by Alembic.
revision = '1f82507200d7'
down_revision = '4ed50e7ac940'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from h import pubid

Session = sessionmaker()

group = sa.table('group',
    sa.column('id', sa.Integer),
    sa.column('pubid', sa.Text),
)


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    # Add new pubids to each row lacking one. This is O(N) but does not lock
    # the whole table.
    for id_, _ in session.query(group).all():
        op.execute(group.update().\
                       where(group.c.id == id_).\
                       where(group.c.pubid == None).\
                       values(pubid=pubid.generate()))

def downgrade():
    # Nothing to do here.
    pass
