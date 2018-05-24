# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from h.search import Search
from h.search import TopLevelAnnotationsFilter


class TestTopLevelAnnotationsFilter(object):

    def test_it_filters_out_replies_but_leaves_annotations_in(self, Annotation, search):
        annotation = Annotation(shared=True)
        reply = Annotation(references=[annotation.id], shared=True)

        result = search.run({})

        assert annotation.id in result.annotation_ids
        assert reply.id not in result.annotation_ids

    @pytest.fixture
    def search(self, pyramid_request):
        search = Search(pyramid_request)
        search.append_filter(TopLevelAnnotationsFilter())
        return search
