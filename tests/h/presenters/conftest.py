# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest


class FakeLinksService(object):
    def __init__(self):
        self.last_annotation = None

    def get(self, annotation, name):
        self.last_annotation = annotation
        return "http://fake-link/" + name

    def get_all(self, annotation):
        self.last_annotation = annotation
        return {"giraffe": "http://giraffe.com", "toad": "http://toad.net"}


@pytest.fixture
def fake_links_service():
    return FakeLinksService()


@pytest.fixture
def group_service():
    return mock.Mock(spec_set=["find"])
