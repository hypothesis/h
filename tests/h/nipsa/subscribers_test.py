# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from collections import namedtuple

import mock
import pytest

from h.nipsa import subscribers

FakeEvent = namedtuple("FakeEvent", ["request", "annotation", "annotation_dict"])


class FakeAnnotation(object):
    def __init__(self, data):
        self.data = data

    @property
    def id(self):
        return self.data["id"]


@pytest.mark.usefixtures("nipsa_service", "moderation_service")
class TestTransformAnnotation(object):
    @pytest.mark.parametrize(
        "ann,flagged",
        [
            (FakeAnnotation({"id": "ann-1", "user": "george"}), True),
            (FakeAnnotation({"id": "ann-2", "user": "georgia"}), False),
            (FakeAnnotation({"id": "ann-3"}), False),
        ],
    )
    def test_with_user_nipsa(self, ann, flagged, nipsa_service, pyramid_request):
        nipsa_service.is_flagged.return_value = flagged
        event = FakeEvent(
            request=pyramid_request, annotation=ann, annotation_dict=ann.data
        )

        subscribers.transform_annotation(event)

        if flagged:
            assert ann.data["nipsa"] is True
        else:
            assert "nipsa" not in ann.data

    @pytest.mark.parametrize(
        "ann,moderated",
        [
            (FakeAnnotation({"id": "normal"}), False),
            (FakeAnnotation({"id": "moderated"}), True),
        ],
    )
    def test_with_moderated_annotation(
        self, ann, moderated, moderation_service, pyramid_request
    ):
        moderation_service.hidden.return_value = moderated
        event = FakeEvent(
            request=pyramid_request, annotation=ann, annotation_dict=ann.data
        )

        subscribers.transform_annotation(event)

        if moderated:
            assert "nipsa" not in ann.data
        else:
            assert "nipsa" not in ann.data

    @pytest.fixture
    def nipsa_service(self, pyramid_config):
        service = mock.Mock(spec_set=["is_flagged"])
        service.is_flagged.return_value = False
        pyramid_config.register_service(service, name="nipsa")
        return service

    @pytest.fixture
    def moderation_service(self, pyramid_config):
        service = mock.Mock(spec_set=["hidden"])
        service.hidden.return_value = False
        pyramid_config.register_service(service, name="annotation_moderation")
        return service
