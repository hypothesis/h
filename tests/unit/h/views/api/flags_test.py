from unittest import mock

import pytest
from pyramid.httpexceptions import HTTPNoContent

from h.traversal import AnnotationContext
from h.views.api import flags as views


@pytest.mark.usefixtures("flag_service")
class TestCreate:
    def test_it(self, annotation_context, pyramid_request, flag_service):
        response = views.create(annotation_context, pyramid_request)

        assert isinstance(response, HTTPNoContent)
        flag_service.create.assert_called_once_with(
            pyramid_request.user, annotation_context.annotation
        )

    @pytest.mark.parametrize("incontext_returns", (True, False))
    def test_it_sends_notification_email(
        self,
        annotation_context,
        pyramid_request,
        flag_notification,
        mailer,
        incontext_link,
        incontext_returns,
    ):
        if not incontext_returns:
            incontext_link.return_value = None

        views.create(annotation_context, pyramid_request)

        flag_notification.generate.assert_called_once_with(
            request=pyramid_request,
            email=annotation_context.annotation.group.creator.email,
            incontext_link=(
                incontext_link.return_value
                if incontext_returns
                else annotation_context.annotation.target_uri
            ),
        )

        mailer.send.delay.assert_called_once_with(
            *flag_notification.generate.return_value
        )

    @pytest.mark.parametrize("blank_field", ("creator", "creator_email"))
    def test_doesnt_send_email_if_group_has_no_creator_or_email(
        self, annotation_context, pyramid_request, mailer, blank_field
    ):
        if blank_field == "creator":
            annotation_context.annotation.group.creator = None
        else:
            annotation_context.annotation.group.creator.email = None

        views.create(annotation_context, pyramid_request)

        assert not mailer.send.delay.called

    @pytest.fixture
    def annotation_context(self, factories):
        return mock.create_autospec(
            AnnotationContext,
            instance=True,
            annotation=factories.Annotation(group=factories.Group()),
        )

    @pytest.fixture
    def pyramid_request(self, factories, pyramid_request, annotation_context):
        pyramid_request.user = factories.User()
        pyramid_request.json_body = {"annotation": annotation_context.annotation.id}
        return pyramid_request

    @pytest.fixture(autouse=True)
    def flag_notification(self, patch):
        return patch("h.views.api.flags.flag_notification")

    @pytest.fixture(autouse=True)
    def mailer(self, patch):
        return patch("h.views.api.flags.mailer")

    @pytest.fixture(autouse=True)
    def incontext_link(self, patch):
        return patch("h.views.api.flags.links.incontext_link")
