import logging
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import create_autospec, sentinel

import pytest
from freezegun import freeze_time
from hubspot.crm.contacts import (
    BatchInputSimplePublicObjectBatchInputUpsert,
    SimplePublicObjectBatchInputUpsert,
)

from h.services.hubspot import HubSpotClient, HubSpotService, factory

NOW = datetime(2026, 10, 9, 12, 0, 0)  # noqa: DTZ001


class TestHubSpotClient:
    def test_it_upserts_the_contacts_by_email(self, client, api_client):
        client.upsert_contacts(
            {"1": {"email": "a@example.edu"}, "2": {"email": "b@example.edu"}}
        )

        api_client.crm.contacts.batch_api.upsert.assert_called_once_with(
            BatchInputSimplePublicObjectBatchInputUpsert(
                inputs=[
                    SimplePublicObjectBatchInputUpsert(
                        id="a@example.edu",
                        id_property="email",
                        object_write_trace_id="1",
                        properties={"email": "a@example.edu"},
                    ),
                    SimplePublicObjectBatchInputUpsert(
                        id="b@example.edu",
                        id_property="email",
                        object_write_trace_id="2",
                        properties={"email": "b@example.edu"},
                    ),
                ]
            )
        )

    def test_it_returns_the_keys_HubSpot_accepted(self, client, api_client):
        api_client.crm.contacts.batch_api.upsert.return_value = SimpleNamespace(
            results=[SimpleNamespace(object_write_trace_id="1")]
        )

        accepted = client.upsert_contacts(
            {"1": {"email": "a@example.edu"}, "2": {"email": "b@example.edu"}}
        )

        assert accepted == {"1"}

    def test_it_logs_the_contacts_HubSpot_rejected(self, client, api_client, caplog):
        api_client.crm.contacts.batch_api.upsert.return_value = SimpleNamespace(
            results=[],
            errors=[
                SimpleNamespace(
                    message="Property values were not valid",
                    context={"objectWriteTraceId": ["1"]},
                )
            ],
        )

        with caplog.at_level(logging.ERROR):
            client.upsert_contacts({"1": {"email": "a@example.edu"}})

        assert caplog.messages == [
            "HubSpot rejected a contact: Property values were not valid ({'objectWriteTraceId': ['1']})"
        ]

    @pytest.fixture
    def api_client(self, mocker):
        # HubSpot builds its API objects on first access, so there's no spec
        # to check this mock against.
        api_client = mocker.Mock()
        api_client.crm.contacts.batch_api.upsert.return_value = SimpleNamespace(
            results=[]
        )
        return api_client

    @pytest.fixture
    def client(self, api_client):
        return HubSpotClient(api_client)


@freeze_time(NOW)
class TestSyncEduRoleContacts:
    def test_it_sends_the_instructors(self, svc, hubspot_client, factories):
        response = factories.UserSurveyResponse(
            user=factories.User(email="teacher@example.edu")
        )

        svc.sync_edu_role_contacts()

        hubspot_client.upsert_contacts.assert_called_once_with(
            {
                str(response.id): {
                    "email": "teacher@example.edu",
                    "web_app_user_id": response.user.userid,
                    "web_app_role": "Instructor",
                    "web_app_id_sync_date": "2026-10-09",
                }
            }
        )
        assert response.hubspot_synced_at == NOW

    def test_it_sends_the_name_from_the_users_Google_account(
        self, svc, hubspot_client, factories
    ):
        user = factories.User()
        factories.UserIdentity(user=user, provider="orcid.org", name="ORCID Name")
        factories.UserIdentity(user=user, provider="google.com", name="Google Name")
        factories.UserSurveyResponse(user=user)

        svc.sync_edu_role_contacts()

        (contact,) = hubspot_client.upsert_contacts.call_args.args[0].values()
        assert contact["web_app_sso_name"] == "Google Name"

    @pytest.mark.parametrize("name", [None, ""])
    def test_it_leaves_out_the_sso_name_if_theres_none(
        self, svc, hubspot_client, factories, name
    ):
        user = factories.User()
        factories.UserIdentity(user=user, provider="google.com", name=name)
        factories.UserSurveyResponse(user=user)

        svc.sync_edu_role_contacts()

        (contact,) = hubspot_client.upsert_contacts.call_args.args[0].values()
        assert "web_app_sso_name" not in contact

    @pytest.mark.parametrize("response", ["not_instructor", "dismissed"])
    def test_it_doesnt_send_other_answers(
        self, svc, hubspot_client, factories, response
    ):
        factories.UserSurveyResponse(response=response)

        svc.sync_edu_role_contacts()

        hubspot_client.upsert_contacts.assert_not_called()

    def test_it_doesnt_send_deleted_users(self, svc, hubspot_client, factories):
        factories.UserSurveyResponse(user=factories.User(deleted=True))

        svc.sync_edu_role_contacts()

        hubspot_client.upsert_contacts.assert_not_called()

    def test_it_doesnt_send_users_without_an_email(
        self, svc, hubspot_client, factories
    ):
        factories.UserSurveyResponse(user=factories.User(email=None))

        svc.sync_edu_role_contacts()

        hubspot_client.upsert_contacts.assert_not_called()

    def test_it_doesnt_send_an_answer_twice(self, svc, hubspot_client, factories):
        factories.UserSurveyResponse(
            responded_at=NOW - timedelta(days=2),
            hubspot_synced_at=NOW - timedelta(days=1),
        )

        svc.sync_edu_role_contacts()

        hubspot_client.upsert_contacts.assert_not_called()

    def test_it_sends_in_batches_and_commits_each_one(
        self, svc, hubspot_client, factories, transaction_manager
    ):
        hubspot_client.MAX_BATCH_SIZE = 2
        responses = factories.UserSurveyResponse.create_batch(3)

        svc.sync_edu_role_contacts()

        assert [
            list(call.args[0]) for call in hubspot_client.upsert_contacts.call_args_list
        ] == [
            [str(responses[0].id), str(responses[1].id)],
            [str(responses[2].id)],
        ]
        assert transaction_manager.commit.call_count == 2

    def test_it_only_marks_the_contacts_HubSpot_accepted(
        self, svc, hubspot_client, factories
    ):
        accepted, rejected = factories.UserSurveyResponse.create_batch(2)
        hubspot_client.upsert_contacts.side_effect = lambda _contacts: {
            str(accepted.id)
        }

        svc.sync_edu_role_contacts()

        assert accepted.hubspot_synced_at == NOW
        assert rejected.hubspot_synced_at is None

    def test_it_doesnt_send_rejected_contacts_again_in_the_same_run(
        self, svc, hubspot_client, factories
    ):
        hubspot_client.MAX_BATCH_SIZE = 1
        factories.UserSurveyResponse.create_batch(2)
        hubspot_client.upsert_contacts.side_effect = lambda _contacts: set()

        svc.sync_edu_role_contacts()

        assert hubspot_client.upsert_contacts.call_count == 2

    def test_it_marks_nothing_if_sending_fails(
        self, svc, hubspot_client, factories, transaction_manager
    ):
        response = factories.UserSurveyResponse()
        hubspot_client.upsert_contacts.side_effect = RuntimeError

        with pytest.raises(RuntimeError):
            svc.sync_edu_role_contacts()

        assert response.hubspot_synced_at is None
        transaction_manager.commit.assert_not_called()

    def test_it_does_nothing_without_an_api_key(
        self, db_session, transaction_manager, factories, caplog
    ):
        factories.UserSurveyResponse()
        svc = HubSpotService(
            session=db_session, transaction_manager=transaction_manager, client=None
        )

        with caplog.at_level(logging.INFO):
            svc.sync_edu_role_contacts()

        assert caplog.messages == [
            "No HubSpot API key configured, not sending contacts"
        ]
        transaction_manager.commit.assert_not_called()

    @pytest.fixture
    def hubspot_client(self):
        hubspot_client = create_autospec(HubSpotClient, instance=True)
        hubspot_client.MAX_BATCH_SIZE = 100
        hubspot_client.upsert_contacts.side_effect = lambda contacts: set(contacts)
        return hubspot_client


@freeze_time(NOW)
class TestCountPendingEduRoleContacts:
    def test_it(self, svc, factories):
        # Pending and old enough: these are counted.
        factories.UserSurveyResponse.create_batch(
            2, responded_at=NOW - timedelta(days=2)
        )
        # Too recent.
        factories.UserSurveyResponse(responded_at=NOW - timedelta(hours=1))
        # Already sent.
        factories.UserSurveyResponse(
            responded_at=NOW - timedelta(days=2),
            hubspot_synced_at=NOW - timedelta(days=1),
        )
        # Not an instructor.
        factories.UserSurveyResponse(
            response="not_instructor", responded_at=NOW - timedelta(days=2)
        )

        assert svc.count_pending_edu_role_contacts(older_than=timedelta(days=1)) == 2

    @pytest.fixture
    def hubspot_client(self):
        return create_autospec(HubSpotClient, instance=True)


class TestFactory:
    @pytest.fixture(autouse=True)
    def pyramid_request(self, pyramid_request):
        pyramid_request.tm = sentinel.tm
        return pyramid_request

    def test_it(self, pyramid_request, HubSpot, HubSpotClient):
        pyramid_request.registry.settings["h.hubspot_api_key"] = sentinel.api_key

        svc = factory(sentinel.context, pyramid_request)

        HubSpot.assert_called_once_with(access_token=sentinel.api_key)
        HubSpotClient.assert_called_once_with(HubSpot.return_value)
        assert svc._session == pyramid_request.db  # noqa: SLF001
        assert svc._transaction_manager == pyramid_request.tm  # noqa: SLF001
        assert svc._client == HubSpotClient.return_value  # noqa: SLF001

    def test_it_without_an_api_key(self, pyramid_request, HubSpotClient):
        svc = factory(sentinel.context, pyramid_request)

        HubSpotClient.assert_not_called()
        assert svc._client is None  # noqa: SLF001

    @pytest.fixture
    def HubSpot(self, patch):
        return patch("h.services.hubspot.HubSpot")

    @pytest.fixture
    def HubSpotClient(self, patch):
        return patch("h.services.hubspot.HubSpotClient")


@pytest.fixture
def transaction_manager(mocker):
    return mocker.Mock(spec_set=["commit"])


@pytest.fixture
def svc(db_session, transaction_manager, hubspot_client):
    return HubSpotService(
        session=db_session,
        transaction_manager=transaction_manager,
        client=hubspot_client,
    )
