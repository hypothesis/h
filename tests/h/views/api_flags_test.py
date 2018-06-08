# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from pyramid.httpexceptions import HTTPNoContent

from h.views import api_flags as views


@pytest.mark.usefixtures(
    "flag_service",
    "group_service",
    "mailer",
    "flag_notification_email",
    "incontext_link",
)
class TestCreate(object):
    def test_it_flags_annotation(self, pyramid_request, flag_service):
        context = mock.Mock()

        views.create(context, pyramid_request)

        flag_service.create.assert_called_once_with(
            pyramid_request.user, context.annotation
        )

    def test_it_returns_no_content(self, pyramid_request):
        context = mock.Mock()

        response = views.create(context, pyramid_request)
        assert isinstance(response, HTTPNoContent)

    def test_passes_info_to_flag_notification_email(
        self, pyramid_request, group_service, flag_notification_email, incontext_link
    ):
        context = mock.Mock()
        pyramid_request.json_body = {"annotation": context.annotation.id}

        views.create(context, pyramid_request)

        flag_notification_email.assert_called_once_with(
            request=pyramid_request,
            email=group_service.find.return_value.creator.email,
            incontext_link=incontext_link.return_value,
        )

    def test_passes_annotation_target_uri_to_flag_notification_email(
        self, pyramid_request, group_service, flag_notification_email, incontext_link
    ):
        context = mock.Mock()
        pyramid_request.json_body = {"annotation": context.annotation.id}
        incontext_link.return_value = None

        views.create(context, pyramid_request)

        flag_notification_email.assert_called_once_with(
            request=pyramid_request,
            email=group_service.find.return_value.creator.email,
            incontext_link=context.annotation.target_uri,
        )

    def test_sends_notification_email(
        self, pyramid_request, flag_notification_email, mailer
    ):
        context = mock.Mock()
        pyramid_request.json_body = {"annotation": context.annotation.id}

        views.create(context, pyramid_request)
        mailer.send.delay.assert_called_once_with(*flag_notification_email.return_value)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.user = mock.Mock()
        pyramid_request.json_body = {}
        return pyramid_request

    @pytest.fixture
    def flag_service(self, pyramid_config):
        flag_service = mock.Mock(spec_set=["create"])
        pyramid_config.register_service(flag_service, name="flag")
        return flag_service

    @pytest.fixture
    def group_service(self, pyramid_config):
        group_service = mock.Mock(spec_set=["find"])
        pyramid_config.register_service(
            group_service, iface="h.interfaces.IGroupService"
        )
        return group_service

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
        return patch("h.views.api_flags.mailer")

    @pytest.fixture
    def incontext_link(self, patch):
        return patch("h.views.api_flags.links.incontext_link")
