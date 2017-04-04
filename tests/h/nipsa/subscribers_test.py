# -*- coding: utf-8 -*-

from collections import namedtuple

import mock
import pytest

from h.nipsa import subscribers

FakeEvent = namedtuple('FakeEvent', ['request', 'annotation_dict'])


@pytest.mark.usefixtures('nipsa_service', 'moderation_service')
class TestTransformAnnotation(object):
    @pytest.mark.parametrize('ann,flagged', [
        ({'id': 'ann-1', 'user': 'george'}, True),
        ({'id': 'ann-2', 'user': 'georgia'}, False),
        ({'id': 'ann-3'}, False),
    ])
    def test_with_user_nipsa(self, ann, flagged, nipsa_service, pyramid_request):
        nipsa_service.is_flagged.return_value = flagged
        event = FakeEvent(request=pyramid_request,
                          annotation_dict=ann)

        subscribers.transform_annotation(event)

        if flagged:
            assert ann['nipsa'] is True
        else:
            assert 'nipsa' not in ann

    @pytest.mark.parametrize('ann,moderated', [
        ({'id': 'normal'}, False),
        ({'id': 'moderated'}, True)
    ])
    def test_with_moderated_annotation(self, ann, moderated, moderation_service, pyramid_request):
        moderation_service.hidden.return_value = moderated
        event = FakeEvent(request=pyramid_request,
                          annotation_dict=ann)

        subscribers.transform_annotation(event)

        if moderated:
            assert ann['nipsa'] is True
        else:
            assert 'nipsa' not in ann

    @pytest.fixture
    def nipsa_service(self, pyramid_config):
        service = mock.Mock(spec_set=['is_flagged'])
        service.is_flagged.return_value = False
        pyramid_config.register_service(service, name='nipsa')
        return service

    @pytest.fixture
    def moderation_service(self, pyramid_config):
        service = mock.Mock(spec_set=['hidden'])
        service.hidden.return_value = False
        pyramid_config.register_service(service, name='annotation_moderation')
        return service
