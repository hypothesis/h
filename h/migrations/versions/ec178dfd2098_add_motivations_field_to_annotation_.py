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


class Motivation(enum.Enum):
    assessing = "assessing"
    bookmarking = "bookmarking"
    classifying = "classifying"
    commenting = "commenting"
    describing = "describing"
    editing = "editing"
    highlighting = "highlighting"
    identifying = "identifying"
    linking = "linking"
    moderating = "moderating"
    questioning = "questioning"
    replying = "replying"
    tagging = "tagging"

motivation_type = sa.Enum(Motivation, name="annotation_motivation")

def upgrade():
    # Create the motivation_type type in db
    motivation_type.create(op.get_bind())
    # Add an Array column whose elements must be a motivation_type
    op.add_column("annotation", sa.Column('motivations',
                    postgresql.ARRAY(motivation_type),
                    server_default=sa.text('ARRAY[]::annotation_motivation[]')
                  ))

def downgrade():
    op.drop_column("annotation", "motivations")
    motivation_type.drop(op.get_bind())
