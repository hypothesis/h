# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h.services import flag_count


class TestFlagCountService(object):
    def test_flag_count_returns_zero_for_unflagged_annotation(self, svc, unflagged):
        assert svc.flag_count(unflagged) == 0

    def test_flag_count_returns_flag_count_for_flagged_annotation(self, svc, flagged):
        assert svc.flag_count(flagged) == 2

    def test_flag_counts_returns_empty_dict_for_no_ids(self, svc):
        assert svc.flag_counts([]) == {}

    def test_flag_counts_returns_all_ids_in_result(self, svc, flagged, unflagged):
        ann_ids = [flagged.id, unflagged.id]

        flag_counts = svc.flag_counts(ann_ids)

        assert set(flag_counts.keys()) == set(ann_ids)

    def test_flag_counts_returns_zero_for_unflagged_annotation(self, svc, unflagged):
        flag_counts = svc.flag_counts([unflagged.id])

        assert flag_counts[unflagged.id] == 0

    def test_flag_counts_returns_flag_count_for_flagged_annotation(self, svc, flagged):
        flag_counts = svc.flag_counts([flagged.id])

        assert flag_counts[flagged.id] == 2

class TestPreloadedFlagCountService(object):

    def test_unflagged_annotation(self, svc, unflagged):
        psvc = flag_count.PreloadedFlagCountService(svc, [unflagged.id])

        assert psvc.flag_count(unflagged) == 0

    def test_flagged_annotation(self, svc, flagged):
        psvc = flag_count.PreloadedFlagCountService(svc, [flagged.id])

        assert psvc.flag_count(flagged) == 2

    def test_unloaded_id(self, svc, unflagged):
        psvc = flag_count.PreloadedFlagCountService(svc, [])

        with pytest.raises(flag_count.NotPreloadedError):
            psvc.flag_count(unflagged)


@pytest.fixture
def svc(db_session):
    return flag_count.FlagCountService(db_session)


@pytest.fixture
def unflagged(factories):
    return factories.Annotation()


@pytest.fixture
def flagged(factories):
    annotation = factories.Annotation()
    factories.Flag.create_batch(2, annotation=annotation)
    return annotation
