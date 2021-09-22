from unittest import mock

import pytest

from h import models
from h.views.admin.features import (
    cohorts_add,
    cohorts_edit,
    cohorts_edit_add,
    cohorts_edit_remove,
    cohorts_index,
    features_index,
    features_save,
)


class DummyFeature:
    def __init__(self, name):
        self.name = name
        self.everyone = False
        self.admins = False
        self.staff = False


features_save_fixtures = pytest.mark.usefixtures("Feature")


def test_features_index_sorts_features(Feature, pyramid_request):
    alpha = DummyFeature(name="alpha")
    beta = DummyFeature(name="beta")
    delta = DummyFeature(name="delta")
    Feature.all.return_value = [beta, delta, alpha]

    ctx = features_index(pyramid_request)

    assert ctx["features"] == [alpha, beta, delta]


@features_save_fixtures
def test_features_save_sets_attributes_when_checkboxes_on(Feature, pyramid_request):
    feature_foo = DummyFeature(name="foo")
    feature_bar = DummyFeature(name="bar")
    Feature.all.return_value = [feature_foo, feature_bar]
    pyramid_request.POST = {
        "foo[everyone]": "on",
        "foo[staff]": "on",
        "bar[admins]": "on",
    }

    features_save(pyramid_request)

    assert feature_foo.everyone is feature_foo.staff is feature_bar.admins is True


@features_save_fixtures
def test_features_save_sets_attributes_when_checkboxes_off(Feature, pyramid_request):
    feature = DummyFeature(name="foo")
    feature.everyone = True
    feature.staff = True
    Feature.all.return_value = [feature]
    pyramid_request.POST = {}

    features_save(pyramid_request)

    assert not feature.everyone
    assert not feature.staff


@features_save_fixtures
def test_features_save_ignores_unknown_fields(Feature, pyramid_request):
    feature = DummyFeature(name="foo")
    Feature.all.return_value = [feature]
    pyramid_request.POST = {"foo[wibble]": "on", "foo[admins]": "ignoreme"}

    features_save(pyramid_request)

    assert not feature.admins


def test_cohorts_index_without_cohorts(pyramid_request):
    result = cohorts_index({}, pyramid_request)
    assert result["results"] == []


def test_cohorts_index_with_cohorts(pyramid_request):
    cohort1 = models.FeatureCohort(name="cohort1")
    cohort2 = models.FeatureCohort(name="cohort2")
    pyramid_request.db.add(cohort1)
    pyramid_request.db.add(cohort2)
    pyramid_request.db.flush()

    result = cohorts_index({}, pyramid_request)
    assert len(result["results"]) == 2


def test_cohorts_add_creates_cohort_with_no_members(pyramid_request):
    pyramid_request.params["add"] = "cohort"
    cohorts_add(pyramid_request)

    result = (
        pyramid_request.db.query(models.FeatureCohort).filter_by(name="cohort").all()
    )
    assert len(result) == 1

    cohort = result[0]
    assert cohort.name == "cohort"
    assert not cohort.members


def test_cohorts_edit_add_user(factories, pyramid_request):
    user = factories.User(username="benoit")
    cohort = models.FeatureCohort(name="FractalCohort")

    pyramid_request.db.add(cohort)
    pyramid_request.db.flush()

    pyramid_request.matchdict["id"] = cohort.id
    pyramid_request.params["add"] = user.username
    pyramid_request.params["authority"] = user.authority
    cohorts_edit_add(pyramid_request)

    assert len(cohort.members) == 1
    assert cohort.members[0].username == user.username


def test_cohorts_edit_add_user_strips_spaces(factories, pyramid_request):
    user = factories.User(username="benoit", authority="foo.org")
    cohort = models.FeatureCohort(name="FractalCohort")

    pyramid_request.db.add(cohort)
    pyramid_request.db.flush()

    pyramid_request.matchdict["id"] = cohort.id
    pyramid_request.params["add"] = "   benoit   "
    pyramid_request.params["authority"] = f"    {user.authority}   "
    cohorts_edit_add(pyramid_request)

    assert len(cohort.members) == 1
    assert cohort.members[0].username == user.username


def test_cohorts_edit_remove_user(factories, pyramid_request):
    user = factories.User(username="benoit", authority="foo.org")
    cohort = models.FeatureCohort(name="FractalCohort")
    cohort.members.append(user)

    pyramid_request.db.add(cohort)
    pyramid_request.db.flush()

    assert len(cohort.members) == 1

    pyramid_request.matchdict["id"] = cohort.id
    pyramid_request.params["remove"] = user.userid
    cohorts_edit_remove(pyramid_request)

    assert not cohort.members


def test_cohorts_edit_with_no_users(pyramid_request):
    cohort = models.FeatureCohort(name="FractalCohort")
    pyramid_request.db.add(cohort)
    pyramid_request.db.flush()

    pyramid_request.matchdict["id"] = cohort.id
    result = cohorts_edit({}, pyramid_request)

    assert result["cohort"].id == cohort.id
    assert not result["cohort"].members


def test_cohorts_edit_with_users(factories, pyramid_request):
    cohort = models.FeatureCohort(name="FractalCohort")
    user1 = factories.User(username="benoit")
    user2 = factories.User(username="emily", authority="foo.org")
    cohort.members.append(user1)
    cohort.members.append(user2)

    pyramid_request.db.add(cohort)
    pyramid_request.db.flush()

    pyramid_request.matchdict["id"] = cohort.id
    result = cohorts_edit({}, pyramid_request)

    assert result["cohort"].id == cohort.id
    assert len(result["cohort"].members) == 2


@mock.patch.dict("h.models.feature.FEATURES", {"feat": "A test feature"})
def test_features_save_sets_cohorts_when_checkboxes_on(pyramid_request):
    feat = models.Feature(name="feat")
    cohort = models.FeatureCohort(name="cohort")

    pyramid_request.db.add(feat)
    pyramid_request.db.add(cohort)
    pyramid_request.db.flush()

    pyramid_request.POST = {"feat[cohorts][cohort]": "on"}
    features_save(pyramid_request)

    feat = pyramid_request.db.query(models.Feature).filter_by(name="feat").first()
    cohort = (
        pyramid_request.db.query(models.FeatureCohort).filter_by(name="cohort").first()
    )

    assert len(feat.cohorts) == 1
    assert cohort in feat.cohorts


@mock.patch.dict("h.models.feature.FEATURES", {"feat": "A test feature"})
def test_features_save_unsets_cohorts_when_checkboxes_off(pyramid_request):
    feat = models.Feature(name="feat")
    cohort = models.FeatureCohort(name="cohort")
    feat.cohorts.append(cohort)

    pyramid_request.db.add(feat)
    pyramid_request.db.add(cohort)
    pyramid_request.db.flush()

    pyramid_request.POST = {"feat[cohorts][cohort]": "off"}
    features_save(pyramid_request)

    feat = pyramid_request.db.query(models.Feature).filter_by(name="feat").first()
    cohort = (
        pyramid_request.db.query(models.FeatureCohort).filter_by(name="cohort").first()
    )

    assert not feat.cohorts
    assert cohort not in feat.cohorts


@pytest.fixture(autouse=True)
def routes(pyramid_config):
    pyramid_config.add_route("admin.features", "/adm/features")
    pyramid_config.add_route("admin.cohorts", "/adm/cohorts")
    pyramid_config.add_route("admin.cohorts_edit", "/adm/cohorts/{id}")


@pytest.fixture
def Feature(patch):
    return patch("h.models.Feature")
