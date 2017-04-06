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

    @pytest.fixture
    def unflagged(self, factories):
        return factories.Annotation()

    @pytest.fixture
    def flagged(self, factories):
        annotation = factories.Annotation()
        factories.Flag.create_batch(2, annotation=annotation)
        return annotation

    @pytest.fixture
    def svc(self, db_session):
        return flag_count.FlagCountService(db_session)
