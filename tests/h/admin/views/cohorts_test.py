# -*- coding: utf-8 -*-

from pyramid import httpexceptions as exc
from pyramid.testing import DummyRequest
import pytest

from h import db
from h.admin.views import cohorts as views


def test_cohorts_index_when_no_cohorts():
    req = DummyRequest()
    result = views.cohorts_index({}, req)
    assert result["results"] == []


def test_new_cohort_creates_cohort():
    req = DummyRequest()
    req.db = db.Session

    req.params['add'] = 'cohort'
    result = views.cohorts_add(req)
    assert isinstance(result, exc.HTTPSeeOther)

    result = views.cohorts_index({}, req)
    assert len(result["results"]) == 1
    assert result["results"][0].name == "cohort"


@pytest.fixture(autouse=True)
def routes(config):
    config.add_route('admin_cohorts', '/adm/cohorts')
