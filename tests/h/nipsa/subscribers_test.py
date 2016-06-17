# -*- coding: utf-8 -*-

from collections import namedtuple

import mock
import pytest
from pyramid.request import apply_request_extensions

from h.nipsa import subscribers

FakeEvent = namedtuple('FakeEvent', ['request', 'annotation_dict'])


@pytest.mark.usefixtures('nipsa_service')
@pytest.mark.parametrize("ann,flagged", [
    ({"user": "george"}, True),
    ({"user": "georgia"}, False),
    ({}, False),
])
def test_transform_annotation(ann, flagged, nipsa_service, pyramid_request):
    nipsa_service.is_flagged.return_value = flagged
    event = FakeEvent(request=pyramid_request,
                      annotation_dict=ann)

    subscribers.transform_annotation(event)

    if flagged:
        assert ann["nipsa"] is True
    else:
        assert "nipsa" not in ann


@pytest.fixture
def nipsa_service(pyramid_config, pyramid_request):
    service = mock.Mock(spec_set=['is_flagged'])
    service.is_flagged.return_value = False

    pyramid_config.include('pyramid_services')
    pyramid_config.register_service(service, name='nipsa')

    apply_request_extensions(pyramid_request)

    return service
