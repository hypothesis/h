import logging
from datetime import datetime, timedelta

from hubspot import HubSpot
from hubspot.crm.contacts import (
    BatchInputSimplePublicObjectBatchInputUpsert,
    SimplePublicObjectBatchInputUpsert,
)
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload
from transaction import TransactionManager

from h.models import User
from h.models.user_identity import IdentityProvider
from h.models.user_survey_response import (
    EduRoleSurveyResponse,
    Survey,
    UserSurveyResponse,
)

log = logging.getLogger(__name__)


class HubSpotClient:
    """A thin wrapper around the HubSpot API client."""

    #: The most contacts HubSpot accepts in one batch request.
    MAX_BATCH_SIZE = 100

    def __init__(self, api_client: HubSpot) -> None:
        self._api_client = api_client

    def upsert_contacts(self, contacts: dict[str, dict[str, str]]) -> set[str]:
        """
        Create or update contacts in HubSpot, matching them by email address.

        :param contacts: each contact's properties, which must include "email",
            keyed by any string the caller wants to identify the contact by
        :return: the keys of the contacts that HubSpot created or updated. The
            ones it rejected are logged and left out.
        """
        response = self._api_client.crm.contacts.batch_api.upsert(
            BatchInputSimplePublicObjectBatchInputUpsert(
                inputs=[
                    SimplePublicObjectBatchInputUpsert(
                        id=properties["email"],
                        id_property="email",
                        object_write_trace_id=key,
                        properties=properties,
                    )
                    for key, properties in contacts.items()
                ]
            )
        )

        # Only a response with some contacts rejected has `errors`.
        for error in getattr(response, "errors", None) or []:
            log.error(
                "HubSpot rejected a contact: %s (%s)", error.message, error.context
            )

        return {result.object_write_trace_id for result in response.results}


class HubSpotService:
    """Send the users who said they're instructors to HubSpot."""

    def __init__(
        self,
        session: Session,
        transaction_manager: TransactionManager,
        client: HubSpotClient | None,
    ) -> None:
        self._session = session
        self._transaction_manager = transaction_manager
        self._client = client

    def sync_edu_role_contacts(self) -> None:
        """
        Send HubSpot every instructor answer it doesn't have yet.

        Answers are sent in batches, and each batch is committed as soon as
        HubSpot accepts it. If this stops half way the next run picks up where
        it left off: at worst it sends some contacts a second time, which is
        harmless because HubSpot updates the contact with the same email.

        Contacts that HubSpot rejects stay unsent, and are tried again on the
        next run.
        """
        if not self._client:
            log.info("No HubSpot API key configured, not sending contacts")
            return

        last_id = 0

        while rows := self._session.execute(
            self._pending_query()
            .where(UserSurveyResponse.id > last_id)
            .options(selectinload(User.identities))
            .order_by(UserSurveyResponse.id)
            .limit(self._client.MAX_BATCH_SIZE)
        ).all():
            # Rows HubSpot rejects stay pending, so moving past the batch by
            # id is what stops this run sending them again.
            last_id = rows[-1].UserSurveyResponse.id

            sent_at = datetime.utcnow()  # noqa: DTZ003

            accepted = self._client.upsert_contacts(
                {
                    str(response.id): _contact_properties(user, sent_at)
                    for response, user in rows
                }
            )

            if accepted:
                self._session.execute(
                    update(UserSurveyResponse)
                    .where(UserSurveyResponse.id.in_([int(id_) for id_ in accepted]))
                    .values(hubspot_synced_at=sent_at)
                )
            self._transaction_manager.commit()

    def count_pending_edu_role_contacts(self, older_than: timedelta) -> int:
        """Return how many instructor answers older than `older_than` HubSpot doesn't have yet."""
        return self._session.scalar(
            self._pending_query()
            .with_only_columns(func.count(UserSurveyResponse.id))
            .where(
                UserSurveyResponse.responded_at < datetime.utcnow() - older_than  # noqa: DTZ003
            )
        )

    @staticmethod
    def _pending_query():
        return (
            select(UserSurveyResponse, User)
            .join(User, User.id == UserSurveyResponse.user_id)
            .where(
                UserSurveyResponse.survey == Survey.EDU_ROLE,
                UserSurveyResponse.response == EduRoleSurveyResponse.INSTRUCTOR,
                UserSurveyResponse.hubspot_synced_at.is_(None),
                User.deleted.is_(False),
                User.email.is_not(None),
            )
        )


def _contact_properties(user: User, sent_at: datetime) -> dict[str, str]:
    properties = {
        "email": user.email,
        "web_app_user_id": user.userid,
        "web_app_role": "Instructor",
        "web_app_id_sync_date": sent_at.date().isoformat(),
    }

    # Left out rather than sent empty, so that it doesn't clear a name the
    # contact already has in HubSpot.
    if sso_name := next(
        (
            identity.name
            for identity in user.identities
            if identity.provider == IdentityProvider.GOOGLE and identity.name
        ),
        None,
    ):
        properties["web_app_sso_name"] = sso_name

    return properties


def factory(_context, request) -> HubSpotService:
    api_key = request.registry.settings.get("h.hubspot_api_key")

    return HubSpotService(
        session=request.db,
        transaction_manager=request.tm,
        client=HubSpotClient(HubSpot(access_token=api_key)) if api_key else None,
    )
