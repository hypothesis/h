"""Remove user last login date default values."""
import datetime

import sqlalchemy as sa
from alembic import op

revision = "3359d7d8ec29"
down_revision = "b9de5c897f73"


def upgrade():
    op.alter_column("user", "last_login_date", nullable=True, server_default=None)


def downgrade():
    op.alter_column(
        "user", "last_login_date", server_default=sa.func.now(), nullable=False
    )
