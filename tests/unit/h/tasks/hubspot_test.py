from datetime import timedelta

import pytest

from h.services.hubspot import HubSpotService
from h.tasks.hubspot import report_num_pending_edu_role_contacts, sync_edu_role_contacts


@pytest.mark.usefixtures("celery")
class TestSyncEduRoleContacts:
    def test_it(self, hubspot_service):
        sync_edu_role_contacts()

        hubspot_service.sync_edu_role_contacts.assert_called_once_with()


@pytest.mark.usefixtures("celery")
class TestReportNumPendingEduRoleContacts:
    def test_it(self, hubspot_service, newrelic):
        report_num_pending_edu_role_contacts()

        hubspot_service.count_pending_edu_role_contacts.assert_called_once_with(
            older_than=timedelta(hours=36)
        )
        newrelic.agent.record_custom_metric.assert_called_once_with(
            "Custom/HubSpot/PendingEduRoleContacts",
            hubspot_service.count_pending_edu_role_contacts.return_value,
        )


@pytest.fixture
def hubspot_service(mock_service):
    return mock_service(HubSpotService)


@pytest.fixture
def celery(patch, pyramid_request):
    cel = patch("h.tasks.hubspot.celery", autospec=False)
    cel.request = pyramid_request
    return cel


@pytest.fixture
def newrelic(patch):
    return patch("h.tasks.hubspot.newrelic")
