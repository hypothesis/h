from unittest.mock import ANY, call, sentinel

import pytest
from pyramid.httpexceptions import HTTPNoContent

from h.models import GroupMembership, GroupMembershipRoles
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
        mailer,
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
        assert mailer.send.delay.call_args_list == [
            call(sentinel.email1, sentinel.subject1, sentinel.text1, sentinel.html1),
            call(sentinel.email2, sentinel.subject2, sentinel.text2, sentinel.html2),
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
        self, context, pyramid_request, group_members_service, flag_notification, mailer
    ):
        group_members_service.get_memberships.return_value = []

        flags.create(context, pyramid_request)

        flag_notification.generate.assert_not_called()
        mailer.send.delay.assert_not_called()

    @pytest.fixture(autouse=True)
    def moderators(self, factories, group_members_service):
        moderators = factories.User.build_batch(2)
        group_members_service.get_memberships.return_value = [
            GroupMembership(user=user) for user in moderators
        ]
        return moderators

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation.build()

    @pytest.fixture
    def context(self, annotation):
        return AnnotationContext(annotation)


@pytest.fixture(autouse=True)
def links(mocker):
    return mocker.patch("h.views.api.flags.links", autospec=True)


@pytest.fixture(autouse=True)
def flag_notification(mocker):
    flag_notification = mocker.patch(
        "h.views.api.flags.flag_notification", autospec=True
    )
    flag_notification.generate.side_effect = [
        (sentinel.email1, sentinel.subject1, sentinel.text1, sentinel.html1),
        (sentinel.email2, sentinel.subject2, sentinel.text2, sentinel.html2),
    ]
    return flag_notification


@pytest.fixture(autouse=True)
def mailer(mocker):
    return mocker.patch("h.views.api.flags.mailer", autospec=True)
