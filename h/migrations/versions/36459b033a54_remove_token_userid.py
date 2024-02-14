"""Remove token.userid."""

from alembic import op

revision = "36459b033a54"
down_revision = "2127515df829"


def upgrade():
    op.drop_column("token", "userid")


def downgrade():
    pass
