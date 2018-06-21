<%text># -*- coding: utf-8 -*-</%text>
"""${message}"""
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from alembic import op
${imports if imports else ""}

revision = "${str(up_revision)}"
down_revision = "${str(down_revision)}"


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
