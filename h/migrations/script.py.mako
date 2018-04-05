"""
${message}
"""

from __future__ import unicode_literals

from alembic import op
${imports if imports else ""}

revision = ${repr(str(up_revision))}
down_revision = ${repr(str(down_revision))}


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
