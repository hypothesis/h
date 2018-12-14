# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from h import models
from h.services.feature import (
    FeatureRequestProperty,
    FeatureService,
    UnknownFeatureError,
    feature_service_factory,
)


class TestFeatureRequestProperty(object):
    def test_single_feature_fetch(self, pyramid_request, feature_service):
        result = pyramid_request.feature("foo")

        feature_service.enabled.assert_called_once_with("foo", user=mock.sentinel.user)
        assert result == feature_service.enabled.return_value

    def test_all_feature_fetch(self, pyramid_request, feature_service):
        result = pyramid_request.feature.all()

        feature_service.all.assert_called_once_with(user=mock.sentinel.user)
        assert result == feature_service.all.return_value

    @pytest.fixture
    def feature_service(self, pyramid_config, pyramid_request):
        svc = mock.Mock(spec_set=feature_service_factory(None, pyramid_request))
        pyramid_config.register_service(svc, name="feature")
        return svc

    @pytest.fixture
    def pyramid_config(self, pyramid_config, pyramid_request):
        from pyramid.request import apply_request_extensions

        pyramid_config.add_request_method(
            FeatureRequestProperty, name="feature", reify=True
        )
        apply_request_extensions(pyramid_request)
        return pyramid_config

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        # Remove the preexisting dummy feature client
        delattr(pyramid_request, "feature")
        pyramid_request.user = mock.sentinel.user
        return pyramid_request


@pytest.mark.usefixtures("features")
class TestFeatureService(object):
    def test_enabled_true_if_overridden(self, db_session):
        svc = FeatureService(session=db_session, overrides=["foo"])

        assert svc.enabled("foo") is True

    def test_enabled_false_if_everyone_false(self, db_session):
        svc = FeatureService(session=db_session)

        assert svc.enabled("foo") is False

    def test_enabled_true_if_everyone_true(self, db_session):
        svc = FeatureService(session=db_session)

        assert svc.enabled("on-for-everyone") is True

    def test_enabled_false_when_admins_true_no_user(self, db_session):
        svc = FeatureService(session=db_session)

        assert svc.enabled("on-for-admins") is False

    def test_enabled_false_when_admins_true_nonadmin_user(self, db_session, factories):
        svc = FeatureService(session=db_session)
        user = factories.User(admin=False)

        assert svc.enabled("on-for-admins", user=user) is False

    def test_enabled_true_when_admins_true_admin_user(self, db_session, factories):
        svc = FeatureService(session=db_session)
        user = factories.User(admin=True)

        assert svc.enabled("on-for-admins", user=user) is True

    def test_enabled_false_when_staff_true_no_user(self, db_session):
        svc = FeatureService(session=db_session)

        assert svc.enabled("on-for-staff") is False

    def test_enabled_false_when_staff_true_nonstaff_user(self, db_session, factories):
        svc = FeatureService(session=db_session)
        user = factories.User(staff=False)

        assert svc.enabled("on-for-staff", user=user) is False

    def test_enabled_true_when_staff_true_staff_user(self, db_session, factories):
        svc = FeatureService(db_session)
        user = factories.User(staff=True)

        assert svc.enabled("on-for-staff", user=user) is True

    def test_enabled_false_when_cohort_no_user(self, db_session):
        svc = FeatureService(db_session)

        assert svc.enabled("on-for-cohort") is False

    def test_enabled_false_when_cohort_user_not_in_cohort(self, db_session, factories):
        svc = FeatureService(db_session)
        user = factories.User()

        assert svc.enabled("on-for-cohort", user=user) is False

    def test_enabled_true_when_cohort_user_in_cohort(
        self, cohort, db_session, factories
    ):
        svc = FeatureService(db_session)
        user = factories.User(cohorts=[cohort])

        assert svc.enabled("on-for-cohort", user=user) is True

    def test_enabled_raises_for_unknown_features(self, db_session):
        svc = FeatureService(session=db_session)

        with pytest.raises(UnknownFeatureError):
            svc.enabled("wibble")

    def test_all_returns_feature_dictionary(self, db_session):
        svc = FeatureService(db_session)

        result = svc.all()

        assert result == {
            "foo": False,
            "bar": False,
            "on-for-everyone": True,
            "on-for-staff": False,
            "on-for-admins": False,
            "on-for-cohort": False,
        }

    def test_all_respects_user_param(self, db_session, factories):
        svc = FeatureService(db_session)
        user = factories.User(staff=True)

        result = svc.all(user=user)

        assert result == {
            "foo": False,
            "bar": False,
            "on-for-everyone": True,
            "on-for-staff": True,
            "on-for-admins": False,
            "on-for-cohort": False,
        }

    @pytest.fixture
    def features(self, cohort, factories, patch):
        model = patch("h.services.feature.models.Feature")
        model.all.return_value = [
            factories.Feature(name="foo"),
            factories.Feature(name="bar"),
            factories.Feature(name="on-for-everyone", everyone=True),
            factories.Feature(name="on-for-staff", staff=True),
            factories.Feature(name="on-for-admins", admins=True),
            factories.Feature(name="on-for-cohort", cohorts=[cohort]),
        ]

    @pytest.fixture
    def cohort(self):
        return models.FeatureCohort(name="cohort")


class TestFeatureServiceFactory(object):
    def test_passes_session(self, pyramid_request):
        svc = feature_service_factory(None, pyramid_request)

        assert svc.session is pyramid_request.db

    def test_passes_overrides_parsed_from_get_params(self, pyramid_request):
        pyramid_request.GET["something-else"] = ""
        pyramid_request.GET["__feature__[foo]"] = ""
        pyramid_request.GET["__feature__[bar]"] = ""

        svc = feature_service_factory(None, pyramid_request)

        assert sorted(svc.overrides) == sorted(["foo", "bar"])

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.user = mock.sentinel.user
        return pyramid_request
