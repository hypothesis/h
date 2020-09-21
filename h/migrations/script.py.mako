"""${message}"""
from alembic import op
${imports if imports else ""}

revision = "${str(up_revision)}"
down_revision = "${str(down_revision)}"


def upgrade():
    ${upgrades if upgrades else "pass"}


def downgrade():
    ${downgrades if downgrades else "pass"}
