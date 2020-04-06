"""Create commands for the bulk tests."""
import factory

from h.h_api.bulk_api import CommandBuilder
from h.h_api.bulk_api.model.command import UpsertCommand

AUTHORITY = "lms.hypothes.is"


def _merge_query(command, authority):
    command.body.attributes.update(command.body.query)
    command.body.attributes["authority"] = authority

    return command


class UserUpsertCommand(factory.Factory):
    class Meta:
        model = UpsertCommand

    username = factory.Sequence(lambda n: f"user_{n}")
    display_name = factory.Sequence(lambda n: f"display_name_{n}")
    authority = AUTHORITY
    query_authority = AUTHORITY
    identities = factory.Sequence(
        lambda n: [{"provider": "provider", "provider_unique_id": f"pid_{n}"}]
    )
    user_ref = factory.Sequence(lambda n: f"user_ref_{n}")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        user_ref = kwargs.pop("user_ref")
        authority = kwargs.pop("authority")
        query_authority = kwargs.pop("query_authority")

        return _merge_query(
            CommandBuilder.user.upsert(
                dict(authority=query_authority, **kwargs), user_ref
            ),
            authority,
        )


class GroupUpsertCommand(factory.Factory):
    class Meta:
        model = UpsertCommand

    name = factory.Sequence(lambda n: f"name_{n}")
    authority = AUTHORITY
    authority_provided_id = factory.Sequence(lambda n: f"ap_id_{n}")
    query_authority = AUTHORITY
    group_ref = factory.Sequence(lambda n: f"group_ref_{n}")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        group_ref = kwargs.pop("group_ref")
        authority = kwargs.pop("authority")
        query_authority = kwargs.pop("query_authority")

        return _merge_query(
            CommandBuilder.group.upsert(
                dict(authority=query_authority, **kwargs), group_ref
            ),
            authority,
        )
