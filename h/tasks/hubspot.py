from datetime import timedelta

import newrelic

from h.services.hubspot import HubSpotService
from h.tasks.celery import celery


@celery.task
def sync_edu_role_contacts():
    """Send HubSpot the users who said they're instructors."""
    celery.request.find_service(HubSpotService).sync_edu_role_contacts()


@celery.task
def report_num_pending_edu_role_contacts():
    """
    Report the number of instructor answers not yet in HubSpot to New Relic.

    This is so that we can set a New Relic alert based on this metric, to know
    when sync_edu_role_contacts() keeps failing to send some contacts without
    raising, for example because HubSpot rejects them. Answers newer than a day
    and a half aren't counted, because the sync may not have run since they
    were given.
    """
    newrelic.agent.record_custom_metric(
        "Custom/HubSpot/PendingEduRoleContacts",
        celery.request.find_service(HubSpotService).count_pending_edu_role_contacts(
            older_than=timedelta(hours=36)
        ),
    )
