# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from pyramid.httpexceptions import HTTPNoContent

from h.views.api import flags as views
from h.services.flag import FlagService
from h.services.groupfinder import GroupfinderService
from h.traversal import AnnotationContext


@pytest.mark.usefixtures(
    "flag_service",
    "groupfinder_service",
    "mailer",
    "flag_notification_email",
    "incontext_link",
)
class TestCreate(object):
    def test_it_flags_annotation(
        self, annotation_context, pyramid_request, flag_service
    ):
        views.create(annotation_context, pyramid_request)

        flag_service.create.assert_called_once_with(
            pyramid_request.user, annotation_context.annotation
        )

    def test_it_returns_no_content(self, annotation_context, pyramid_request):
        response = views.create(annotation_context, pyramid_request)

        assert isinstance(response, HTTPNoContent)

    def test_passes_info_to_flag_notification_email(
        self,
        annotation_context,
        pyramid_request,
        groupfinder_service,
        flag_notification_email,
        incontext_link,
    ):
        pyramid_request.json_body = {"annotation": annotation_context.annotation.id}

        views.create(annotation_context, pyramid_request)

        flag_notification_email.assert_called_once_with(
            request=pyramid_request,
            email=groupfinder_service.find.return_value.creator.email,
            incontext_link=incontext_link.return_value,
        )

    def test_passes_annotation_target_uri_to_flag_notification_email(
        self,
        annotation_context,
        pyramid_request,
        groupfinder_service,
        flag_notification_email,
        incontext_link,
    ):
        pyramid_request.json_body = {"annotation": annotation_context.annotation.id}
        incontext_link.return_value = None

        views.create(annotation_context, pyramid_request)

        flag_notification_email.assert_called_once_with(
            request=pyramid_request,
            email=groupfinder_service.find.return_value.creator.email,
            incontext_link=annotation_context.annotation.target_uri,
        )

    def test_sends_notification_email(
        self, annotation_context, pyramid_request, flag_notification_email, mailer
    ):
        pyramid_request.json_body = {"annotation": annotation_context.annotation.id}

        views.create(annotation_context, pyramid_request)

        mailer.send.delay.assert_called_once_with(*flag_notification_email.return_value)

    def test_doesnt_send_email_if_group_has_no_creator(
        self,
        annotation_context,
        factories,
        groupfinder_service,
        pyramid_request,
        mailer,
    ):
        groupfinder_service.find.return_value = factories.Group()
        groupfinder_service.find.return_value.creator = None

        views.create(annotation_context, pyramid_request)

        assert not mailer.send.delay.called

    def test_doesnt_send_email_if_group_creator_has_no_email_address(
        self,
        annotation_context,
        factories,
        groupfinder_service,
        pyramid_request,
        mailer,
    ):
        groupfinder_service.find.return_value = factories.Group(
            creator=factories.User(email=None)
        )

        views.create(annotation_context, pyramid_request)

        assert not mailer.send.delay.called

    @pytest.fixture
    def annotation_context(self, factories):
        return mock.create_autospec(
            AnnotationContext, instance=True, annotation=factories.Annotation()
        )

    @pytest.fixture
    def pyramid_request(self, factories, pyramid_request):
        pyramid_request.user = factories.User()
        pyramid_request.json_body = {}
        return pyramid_request

    @pytest.fixture
    def flag_service(self, pyramid_config):
        flag_service = mock.create_autospec(FlagService, instance=True, spec_set=True)
        pyramid_config.register_service(flag_service, name="flag")
        return flag_service

    @pytest.fixture
    def groupfinder_service(self, pyramid_config):
        groupfinder_service = mock.create_autospec(
            GroupfinderService, instance=True, spec_set=True
        )
        pyramid_config.register_service(
            groupfinder_service, iface="h.interfaces.IGroupService"
        )
        return groupfinder_service

    @pytest.fixture
    def flag_notification_email(self, patch):
        return patch(
            "h.emails.flag_notification.generate",
            return_value=(
                ["fake@example.com"],
                "Some subject",
                "Some text",
                "Some html",
            ),
        )

    @pytest.fixture
    def mailer(self, patch):
        return patch("h.views.api.flags.mailer")

    @pytest.fixture
    def incontext_link(self, patch):
        return patch("h.views.api.flags.links.incontext_link")
