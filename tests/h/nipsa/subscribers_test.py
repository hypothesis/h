# -*- coding: utf-8 -*-

from collections import namedtuple

import mock
import pytest

from h.nipsa import subscribers


FakeEvent = namedtuple('FakeEvent', ['annotation_dict'])


@pytest.mark.parametrize("ann,nipsa", [
    ({"user": "george"}, True),
    ({"user": "georgia"}, False),
    ({}, False),
])
def test_transform_annotation(ann, nipsa, has_nipsa):
    event = FakeEvent(annotation_dict=ann)
    has_nipsa.return_value = nipsa
    subscribers.transform_annotation(event)
    if nipsa:
        assert ann["nipsa"] is True
    else:
        assert "nipsa" not in ann


@pytest.fixture
def has_nipsa(patch):
    return patch('h.nipsa.logic.has_nipsa')
