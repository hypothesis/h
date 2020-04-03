from h.h_api.bulk_api import CommandBuilder


class CommandFactory:
    """Create commands for the bulk tests."""

    AUTHORITY = "lms.hypothes.is"

    @classmethod
    def user_upsert(
        cls, number=0, authority=AUTHORITY, query_authority=AUTHORITY, extras=None
    ):
        attrs = cls._add_extras(
            {
                "username": f"user_{number}",
                "display_name": f"display_name_{number}",
                "authority": query_authority,
                "identities": [
                    {"provider": "provider", "provider_unique_id": f"pid_{number}"}
                ],
            },
            extras,
        )

        return cls._merge_query(
            CommandBuilder.user.upsert(attrs, f"user_ref_{number}"), authority
        )

    @classmethod
    def group_upsert(
        cls, number=0, authority=AUTHORITY, query_authority=AUTHORITY, extras=None
    ):
        attrs = cls._add_extras(
            {
                "name": f"name_{number}",
                "authority": query_authority,
                "authority_provided_id": f"ap_id_{number}",
            },
            extras,
        )

        return cls._merge_query(
            CommandBuilder.group.upsert(attrs, f"group_ref_{number}",), authority,
        )

    @staticmethod
    def _add_extras(base, extras):
        if extras:
            base.update(extras)

        return base

    @staticmethod
    def _merge_query(command, authority):
        command.body.attributes.update(command.body.query)
        command.body.attributes["authority"] = authority

        return command
