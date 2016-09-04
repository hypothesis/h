"""
adding domain column in table document_uri

Revision ID: d6a2a47e76c4
Revises: afd433075707
Create Date: 2016-09-04 20:39:11.391549
"""

from __future__ import unicode_literals

from alembic import op
import sqlalchemy as sa

revision = 'd6a2a47e76c4'
down_revision = 'afd433075707'


def upgrade():
    """Adding domain column to table document_uri"""
    op.add_column(
        'document_uri',
         sa.Column('domain', sa.String(), nullable=False)
    )

def downgrade():
    op.drop_column('document_uri', 'domain')
