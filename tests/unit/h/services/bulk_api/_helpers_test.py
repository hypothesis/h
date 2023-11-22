from unittest.mock import sentinel

import pytest
from _pytest.mark import param
from h_matchers import Any
from sqlalchemy import select

from h.models import Annotation
from h.services.bulk_api._helpers import date_match
from h.services.bulk_api.exceptions import BadDateFilter


class TestDateMatch:
    @pytest.mark.parametrize(
        "spec,expected",
        (
            param({"gt": "2001-01-01"}, ["2"], id="gt"),
            param({"gte": "2001-01-01"}, ["1", "2"], id="gte"),
            param({"lt": "2001-01-01"}, ["0"], id="lt"),
            param({"lte": "2001-01-01"}, ["0", "1"], id="lte"),
            param({"eq": "2001-01-01"}, ["1"], id="eq"),
            param({"ne": "2001-01-01"}, ["0", "2"], id="ne"),
            param({"gt": "2000-01-01", "lt": "2002-01-01"}, ["1"], id="combo"),
        ),
    )
    def test_it(self, db_session, factories, spec, expected):
        factories.Annotation(text="0", created="2000-01-01")
        factories.Annotation(text="1", created="2001-01-01")
        factories.Annotation(text="2", created="2002-01-01")

        annotations = (
            db_session.execute(
                select(Annotation).where(date_match(Annotation.created, spec))
            )
            .scalars()
            .all()
        )

        assert [anno.text for anno in annotations] == Any.list.containing(
            expected
        ).only()

    @pytest.mark.parametrize(
        "bad_spec",
        (
            param({}, id="empty"),
            param({"bad_op": "2002-01-01"}, id="bad_op"),
        ),
    )
    def test_it_raises_for_bad_spec(self, bad_spec):
        with pytest.raises(BadDateFilter):
            date_match(sentinel.column, bad_spec)
