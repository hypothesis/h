"""Rename constraints

Revision ID: 5aab7692b5de
Revises: 571394188821
Create Date: 2015-10-22 16:50:08.158964

"""

# revision identifiers, used by Alembic.
revision = '5aab7692b5de'
down_revision = '571394188821'

from alembic import op
import sqlalchemy as sa


def rename_constraint(op, table, before, after):
    op.execute(sa.text('ALTER TABLE public.{table} '
                       'RENAME CONSTRAINT {before} '
                       'TO {after}'.format(table=table,
                                           before=before,
                                           after=after)))


def upgrade():
    # activation
    rename_constraint(op, 'activation', 'activation_pkey', 'pk__activation')
    rename_constraint(op, 'activation', 'activation_code_key', 'uq__activation__code')

    # blocklist
    rename_constraint(op, 'blocklist', 'blocklist_pkey', 'pk__blocklist')
    rename_constraint(op, 'blocklist', 'blocklist_uri_key', 'uq__blocklist__uri')

    # feature
    rename_constraint(op, 'feature', 'feature_pkey', 'pk__feature')
    rename_constraint(op, 'feature', 'feature_name_key', 'uq__feature__name')

    # group
    rename_constraint(op, 'group', 'group_pkey', 'pk__group')
    rename_constraint(op, 'group', 'group_creator_id_fkey', 'fk__group__creator_id__user')

    # nipsa
    rename_constraint(op, 'nipsa', 'nipsa_pkey', 'pk__nipsa')

    # subscriptions
    rename_constraint(op, 'subscriptions', 'subscriptions_pkey', 'pk__subscriptions')

    # user
    rename_constraint(op, 'user', 'user_pkey', 'pk__user')
    rename_constraint(op, 'user', 'user_email_key', 'uq__user__email')
    rename_constraint(op, 'user', 'user_uid_key', 'uq__user__uid')
    rename_constraint(op, 'user', 'user_username_key', 'uq__user__username')
    rename_constraint(op, 'user', 'user_activation_id_fkey', 'fk__user__activation_id__activation')

    # user_group
    rename_constraint(op, 'user_group', 'user_group_group_id_fkey', 'fk__user_group__group_id__group')
    rename_constraint(op, 'user_group', 'user_group_user_id_fkey', 'fk__user_group__user_id__user')


def downgrade():
    # activation
    rename_constraint(op, 'activation', 'pk__activation', 'activation_pkey')
    rename_constraint(op, 'activation', 'uq__activation__code', 'activation_code_key')

    # blocklist
    rename_constraint(op, 'blocklist', 'pk__blocklist', 'blocklist_pkey')
    rename_constraint(op, 'blocklist', 'uq__blocklist__uri', 'blocklist_uri_key')

    # feature
    rename_constraint(op, 'feature', 'pk__feature', 'feature_pkey')
    rename_constraint(op, 'feature', 'uq__feature__name', 'feature_name_key')

    # group
    rename_constraint(op, 'group', 'pk__group', 'group_pkey')
    rename_constraint(op, 'group', 'fk__group__creator_id__user', 'group_creator_id_fkey')

    # nipsa
    rename_constraint(op, 'nipsa', 'pk__nipsa', 'nipsa_pkey')

    # subscriptions
    rename_constraint(op, 'subscriptions', 'pk__subscriptions', 'subscriptions_pkey')

    # user
    rename_constraint(op, 'user', 'pk__user', 'user_pkey')
    rename_constraint(op, 'user', 'uq__user__email', 'user_email_key')
    rename_constraint(op, 'user', 'uq__user__uid', 'user_uid_key')
    rename_constraint(op, 'user', 'uq__user__username', 'user_username_key')
    rename_constraint(op, 'user', 'fk__user__activation_id__activation', 'user_activation_id_fkey')

    # user_group
    rename_constraint(op, 'user_group', 'fk__user_group__group_id__group', 'user_group_group_id_fkey')
    rename_constraint(op, 'user_group', 'fk__user_group__user_id__user', 'user_group_user_id_fkey')
