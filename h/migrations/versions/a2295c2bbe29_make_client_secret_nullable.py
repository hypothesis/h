"""
Make Client.secret nullable

Revision ID: a2295c2bbe29
Revises: 05bd63575f19
Create Date: 2017-07-18 11:15:39.885020
"""

from __future__ import unicode_literals

from alembic import op


revision = 'a2295c2bbe29'
down_revision = '05bd63575f19'


def upgrade():
    op.alter_column('authclient', 'secret', nullable=True)


def downgrade():
    op.alter_column('authclient', 'secret', nullable=False)
