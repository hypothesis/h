from unittest.mock import ANY, call, create_autospec, sentinel

import pytest
from pyramid.httpexceptions import HTTPNoContent

from h.models import GroupMembership, GroupMembershipRoles
from h.services.email import EmailData, EmailTag
from h.tasks import email
from h.traversal import AnnotationContext
from h.views.api import flags


@pytest.mark.usefixtures("flag_service", "group_members_service")
class TestCreate:
    def test_it(
        self,
        annotation,
        context,
        pyramid_request,
        flag_service,
        links,
        group_members_service,
        tasks_email,
        flag_notification,
        moderators,
    ):
        response = flags.create(context, pyramid_request)

        flag_service.create.assert_called_once_with(pyramid_request.user, annotation)
        links.incontext_link.assert_called_once_with(pyramid_request, annotation)
        group_members_service.get_memberships.assert_called_once_with(
            annotation.group,
            roles=[
                GroupMembershipRoles.OWNER,
                GroupMembershipRoles.ADMIN,
                GroupMembershipRoles.MODERATOR,
            ],
        )
        assert flag_notification.generate.call_args_list == [
            call(pyramid_request, user.email, links.incontext_link.return_value)
            for user in moderators
        ]

        assert tasks_email.send.delay.call_args_list == [
            call(
                {
                    "recipients": [sentinel.email1],
                    "subject": sentinel.subject1,
                    "body": sentinel.text1,
                    "tag": EmailTag.FLAG_NOTIFICATION,
                    "html": sentinel.html1,
                    "subaccount": None,
                },
                {
                    "sender_id": pyramid_request.user.id,
                    "tag": EmailTag.FLAG_NOTIFICATION,
                    "recipient_ids": [moderators[0].id],
                    "extra": {"annotation_id": annotation.id},
                },
            ),
            call(
                {
                    "recipients": [sentinel.email2],
                    "subject": sentinel.subject2,
                    "body": sentinel.text2,
                    "tag": EmailTag.FLAG_NOTIFICATION,
                    "html": sentinel.html2,
                    "subaccount": None,
                },
                {
                    "sender_id": pyramid_request.user.id,
                    "tag": EmailTag.FLAG_NOTIFICATION,
                    "recipient_ids": [moderators[1].id],
                    "extra": {"annotation_id": annotation.id},
                },
            ),
        ]
        assert isinstance(response, HTTPNoContent)

    def test_when_the_annotation_has_no_incontext_link(
        self, context, pyramid_request, links, annotation, flag_notification
    ):
        links.incontext_link.return_value = None

        flags.create(context, pyramid_request)

        assert flag_notification.generate.call_args[0][2] == annotation.target_uri

    def test_when_a_moderator_has_no_email(
        self, context, pyramid_request, moderators, flag_notification
    ):
        moderators[0].email = None

        flags.create(context, pyramid_request)

        assert flag_notification.generate.call_args_list == [
            call(ANY, moderators[1].email, ANY)
        ]

    def test_when_there_are_no_moderators(
        self,
        context,
        pyramid_request,
        group_members_service,
        flag_notification,
        tasks_email,
    ):
        group_members_service.get_memberships.return_value = []

        flags.create(context, pyramid_request)

        flag_notification.generate.assert_not_called()
        tasks_email.send.delay.assert_not_called()

    @pytest.fixture(autouse=True)
    def moderators(self, factories, group_members_service, db_session):
        moderators = factories.User.create_batch(2)
        group = factories.Group()
        memberships = [GroupMembership(user=user, group=group) for user in moderators]
        for membership in memberships:
            db_session.add(membership)
        group_members_service.get_memberships.return_value = memberships
        db_session.commit()
        return moderators

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation.build()

    @pytest.fixture
    def context(self, annotation):
        return AnnotationContext(annotation)

    @pytest.fixture
    def user(self, factories, db_session):
        user = factories.User.create()
        db_session.commit()
        return user

    @pytest.fixture
    def pyramid_request(self, pyramid_request, user):
        pyramid_request.user = user
        return pyramid_request


@pytest.fixture(autouse=True)
def links(mocker):
    return mocker.patch("h.views.api.flags.links", autospec=True)


@pytest.fixture(autouse=True)
def flag_notification(mocker):
    flag_notification = mocker.patch(
        "h.views.api.flags.flag_notification", autospec=True
    )
    flag_notification.generate.side_effect = [
        EmailData(
            recipients=[sentinel.email1],
            subject=sentinel.subject1,
            body=sentinel.text1,
            tag=EmailTag.FLAG_NOTIFICATION,
            html=sentinel.html1,
        ),
        EmailData(
            recipients=[sentinel.email2],
            subject=sentinel.subject2,
            body=sentinel.text2,
            tag=EmailTag.FLAG_NOTIFICATION,
            html=sentinel.html2,
        ),
    ]
    return flag_notification


@pytest.fixture(autouse=True)
def tasks_email(patch):
    mock = patch("h.views.api.flags.email")
    mock.send.delay = create_autospec(email.send.run)
    return mock
