# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h.services.annotation_stats import AnnotationStatsService
from h.services.annotation_stats import annotation_stats_factory
from h.search import Search
from h.search import TopLevelAnnotationsFilter


class TestAnnotationStatsService(object):
    def test_user_annotation_counts_returns_count_of_annotations_for_user(self, svc, factories):
        userid = '123'
        for i in range(3):
            factories.Annotation(userid=userid, shared=True)
        for i in range(2):
            factories.Annotation(userid=userid, shared=False)
        for i in range(4):
            factories.Annotation(userid=userid, groupid='abc', shared=True)

        results = svc.user_annotation_counts(userid)

        assert results['public'] == 3
        assert results['private'] == 2
        assert results['group'] == 4

    @pytest.mark.parametrize('public,group,private,expected_total', [
        (3, 2, 4, 9),
        (3, 2, 0, 5),
        (3, 0, 4, 7),
        (0, 2, 4, 6),
     ])
    def test_user_annotation_counts_includes_total_count_of_annotations_for_user(
            self, svc, factories, public, group, private, expected_total):
        userid = '123'
        for i in range(public):
            factories.Annotation(userid=userid, shared=True)
        for i in range(private):
            factories.Annotation(userid=userid, shared=False)
        for i in range(group):
            factories.Annotation(userid=userid, groupid='abc', shared=True)

        results = svc.user_annotation_counts(userid)

        assert results['total'] == expected_total

    def test_user_annotation_counts_returns_default_values(self, svc, factories):
        results = svc.user_annotation_counts('123')

        assert results['public'] == 0
        assert results['private'] == 0
        assert results['group'] == 0
        assert results['total'] == 0

    def test_user_annotation_counts_ignores_deleted_annotations(self, svc, factories):
        userid = '123'
        for i in range(3):
            factories.Annotation(userid=userid, deleted=True, shared=True)
        for i in range(2):
            factories.Annotation(userid=userid, deleted=True, shared=False)
        for i in range(4):
            factories.Annotation(userid=userid, deleted=True, groupid='abc', shared=True)

        results = svc.user_annotation_counts(userid)

        assert results['public'] == 0
        assert results['private'] == 0
        assert results['group'] == 0
        assert results['total'] == 0

    def test_group_annotation_count_calls_search_with_request_and_stats(
        self, svc, search, pyramid_request,
    ):
        svc.group_annotation_count('groupid')

        search.assert_called_with(pyramid_request, stats=pyramid_request.stats)

    def test_group_annotation_count_calls_run_with_groupid_and_limit(
        self, svc, search,
    ):
        svc.group_annotation_count('groupid')

        search.return_value.run.assert_called_with({"limit": 0, "group": "groupid"})

    def test_group_annotation_count_excludes_replies(
        self, svc, search, top_level_annotation_filter,
    ):
        svc.group_annotation_count('groupid')

        search.return_value.append_modifier.assert_called_with(
            top_level_annotation_filter.return_value)

    def test_group_annotation_count_returns_total(
        self, svc, search,
    ):
        search.return_value.run.return_value.total = 3

        anns = svc.group_annotation_count('groupid')

        assert anns == 3


class TestAnnotationStatsFactory(object):
    def test_returns_service(self):
        svc = annotation_stats_factory(mock.Mock(), mock.Mock())

        assert isinstance(svc, AnnotationStatsService)

    def test_sets_request(self):
        request = mock.Mock()
        svc = annotation_stats_factory(mock.Mock(), request)

        assert svc.request == request


@pytest.fixture
def svc(pyramid_request):
    return AnnotationStatsService(request=pyramid_request)


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.stats = mock.Mock()
    return pyramid_request


@pytest.fixture
def search(patch):
    return patch('h.services.annotation_stats.Search',
                 autospec=Search, spec_set=True)


@pytest.fixture
def top_level_annotation_filter(patch):
    return patch('h.services.annotation_stats.TopLevelAnnotationsFilter',
                 autospec=TopLevelAnnotationsFilter, spec_set=True)
