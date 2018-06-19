"""
Add motivations field to annotation table
"""

from __future__ import unicode_literals

import enum

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "ec178dfd2098"
down_revision = "178270e3ee58"

def upgrade():
    # Add an Array column
    # Ideally, the items should be enum'd, but SQLAlchemy does not support
    # ARRAY with ENUM; validation is at model level
    op.add_column("annotation", sa.Column('motivations',
                    postgresql.ARRAY(sa.UnicodeText, zero_indexes=True)
                  ))

def downgrade():
    op.drop_column("annotation", "motivations")
