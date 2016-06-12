# -*- coding: utf-8 -*-

from pyramid.testing import DummyRequest
import pytest

from h import db
from h import models
from h.admin.views import features as views


class DummyFeature(object):
    def __init__(self, name):
        self.name = name
        self.everyone = False
        self.admins = False
        self.staff = False


features_save_fixtures = pytest.mark.usefixtures('Feature',
                                                 'check_csrf_token')


@features_save_fixtures
def test_features_save_sets_attributes_when_checkboxes_on(Feature, req):
    foo = DummyFeature(name='foo')
    bar = DummyFeature(name='bar')
    Feature.all.return_value = [foo, bar]
    req.POST = {'foo[everyone]': 'on',
                'foo[staff]': 'on',
                'bar[admins]': 'on'}

    views.features_save(req)

    assert foo.everyone == foo.staff == bar.admins == True


@features_save_fixtures
def test_features_save_sets_attributes_when_checkboxes_off(Feature, req):
    foo = DummyFeature(name='foo')
    foo.everyone = True
    foo.staff = True
    Feature.all.return_value = [foo]
    req.POST = {}

    views.features_save(req)

    assert foo.everyone == foo.staff == False


@features_save_fixtures
def test_features_save_ignores_unknown_fields(Feature, req):
    foo = DummyFeature(name='foo')
    Feature.all.return_value = [foo]
    req.POST = {'foo[wibble]': 'on',
                'foo[admins]': 'ignoreme'}

    views.features_save(req)

    assert foo.admins == False


@features_save_fixtures
def test_features_save_checks_csrf_token(Feature, check_csrf_token, req):
    Feature.all.return_value = []
    req.POST = {}

    views.features_save(req)

    check_csrf_token.assert_called_with(req)


def test_cohorts_index_without_cohorts(req):
    result = views.cohorts_index({}, req)
    assert result["results"] == []


def test_cohorts_index_with_cohorts(req):
    cohort1 = models.FeatureCohort(name='cohort1')
    cohort2 = models.FeatureCohort(name='cohort2')
    req.db.add(cohort1)
    req.db.add(cohort2)
    req.db.flush()

    result = views.cohorts_index({}, req)
    assert len(result["results"]) == 2


def test_cohorts_add_creates_cohort_with_no_members(req):
    req.params['add'] = 'cohort'
    views.cohorts_add(req)

    result = req.db.query(models.FeatureCohort).filter_by(name='cohort').all()
    assert len(result) == 1

    cohort = result[0]
    assert cohort.name == "cohort"
    assert len(cohort.members) == 0


def test_cohorts_edit_add_user(req):
    user = models.User(username='benoit',
                       password='mandelbrot',
                       email='benoit@example.com')
    cohort = models.FeatureCohort(name='FractalCohort')

    req.db.add(user)
    req.db.add(cohort)
    req.db.flush()

    req.matchdict['id'] = cohort.id
    req.params['add'] = user.username
    views.cohorts_edit_add(req)

    assert len(cohort.members) == 1
    assert cohort.members[0].username == user.username


def test_cohorts_edit_remove_user(req):
    user = models.User(username='benoit',
                       password='mandelbrot',
                       email='benoit@example.com')
    cohort = models.FeatureCohort(name='FractalCohort')
    cohort.members.append(user)

    req.db.add(user)
    req.db.add(cohort)
    req.db.flush()

    assert len(cohort.members) == 1

    req.matchdict['id'] = cohort.id
    req.params['remove'] = user.username
    views.cohorts_edit_remove(req)

    assert len(cohort.members) == 0


def test_cohorts_edit_with_no_users(req):
    cohort = models.FeatureCohort(name='FractalCohort')
    req.db.add(cohort)
    req.db.flush()

    req.matchdict['id'] = cohort.id
    result = views.cohorts_edit({}, req)

    assert result['cohort'].id == cohort.id
    assert len(result['cohort'].members) == 0


def test_cohorts_edit_with_users(req):
    cohort = models.FeatureCohort(name='FractalCohort')
    user1 = models.User(username='benoit',
                        password='mandelbrot',
                        email='benoit@example.com')
    user2 = models.User(username='emily',
                        password='noether',
                        email='emily@example.com')
    cohort.members.append(user1)
    cohort.members.append(user2)

    db.Session.add(user1)
    db.Session.add(user2)
    db.Session.add(cohort)
    db.Session.flush()

    req.matchdict['id'] = cohort.id
    result = views.cohorts_edit({}, req)

    assert result['cohort'].id == cohort.id
    assert len(result['cohort'].members) == 2


@pytest.fixture
def req(db_session):
    return DummyRequest(db=db_session)


@pytest.fixture(autouse=True)
def routes(config):
    config.add_route('admin_features', '/adm/features')
    config.add_route('admin_cohorts', '/adm/cohorts')
    config.add_route('admin_cohorts_edit', '/adm/cohorts/{id}')


@pytest.fixture
def Feature(patch):
    return patch('h.models.Feature')


@pytest.fixture
def check_csrf_token(patch):
    return patch('pyramid.session.check_csrf_token')
