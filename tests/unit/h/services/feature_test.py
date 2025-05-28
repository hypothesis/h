from unittest import mock

import pytest
from pyramid.request import apply_request_extensions

from h import models
from h.services.feature import (
    FeatureRequestProperty,
    FeatureService,
    UnknownFeatureError,
    feature_service_factory,
)


class TestFeatureRequestProperty:
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
class TestFeatureService:
    def test_enable_feature_via_override(self, db_session):
        svc = FeatureService(session=db_session, overrides={"foo": True})

        assert svc.enabled("foo", user=None) is True

    def test_enabled_false_if_everyone_false(self, db_session):
        svc = FeatureService(session=db_session)

        assert not svc.enabled("foo", user=None)

    def test_enabled_true_if_everyone_true(self, db_session):
        svc = FeatureService(session=db_session)

        assert svc.enabled("on-for-everyone", user=None) is True

    def test_disable_feature_via_override(self, db_session):
        svc = FeatureService(session=db_session, overrides={"on-for-everyone": False})

        assert svc.enabled("on-for-everyone", user=None) is False

    def test_enabled_if_first_party(self, db_session, factories):
        user = factories.User(authority="foobar.com")
        third_party_user = factories.User(authority="othersite.com")
        svc = FeatureService(session=db_session, default_authority=user.authority)

        assert svc.enabled("on-for-first-party", user=None) is False
        assert svc.enabled("on-for-first-party", user) is True
        assert svc.enabled("on-for-first-party", third_party_user) is False

    def test_enabled_false_when_admins_true_no_user(self, db_session):
        svc = FeatureService(session=db_session)

        assert not svc.enabled("on-for-admins", user=None)

    def test_enabled_false_when_admins_true_nonadmin_user(self, db_session, factories):
        svc = FeatureService(session=db_session)
        user = factories.User(admin=False)

        assert not svc.enabled("on-for-admins", user=user)

    def test_enabled_true_when_admins_true_admin_user(self, db_session, factories):
        svc = FeatureService(session=db_session)
        user = factories.User(admin=True)

        assert svc.enabled("on-for-admins", user=user) is True

    def test_enabled_false_when_staff_true_no_user(self, db_session):
        svc = FeatureService(session=db_session)

        assert not svc.enabled("on-for-staff", user=None)

    def test_enabled_false_when_staff_true_nonstaff_user(self, db_session, factories):
        svc = FeatureService(session=db_session)
        user = factories.User(staff=False)

        assert not svc.enabled("on-for-staff", user=user)

    def test_enabled_true_when_staff_true_staff_user(self, db_session, factories):
        svc = FeatureService(db_session)
        user = factories.User(staff=True)

        assert svc.enabled("on-for-staff", user=user) is True

    def test_enabled_false_when_cohort_no_user(self, db_session):
        svc = FeatureService(db_session)

        assert not svc.enabled("on-for-cohort", user=None)

    def test_enabled_false_when_cohort_user_not_in_cohort(self, db_session, factories):
        svc = FeatureService(db_session)
        user = factories.User()

        assert not svc.enabled("on-for-cohort", user=user)

    def test_enabled_true_when_cohort_user_in_cohort(
        self, cohort, db_session, factories
    ):
        svc = FeatureService(db_session)
        user = factories.User(cohorts=[cohort])

        assert svc.enabled("on-for-cohort", user=user) is True

    def test_enabled_raises_for_unknown_features(self, db_session):
        svc = FeatureService(session=db_session)

        with pytest.raises(UnknownFeatureError):
            svc.enabled("wibble", user=None)

    def test_all_returns_feature_dictionary(self, db_session):
        svc = FeatureService(db_session)

        result = svc.all()

        assert result == {
            "foo": False,
            "bar": False,
            "on-for-everyone": True,
            "on-for-first-party": False,
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
            "on-for-first-party": False,
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
            factories.Feature(name="on-for-first-party", first_party=True),
            factories.Feature(name="on-for-staff", staff=True),
            factories.Feature(name="on-for-admins", admins=True),
            factories.Feature(name="on-for-cohort", cohorts=[cohort]),
        ]

    @pytest.fixture
    def cohort(self):
        return models.FeatureCohort(name="cohort")


class TestFeatureServiceFactory:
    def test_passes_session(self, pyramid_request):
        svc = feature_service_factory(None, pyramid_request)

        assert svc.session is pyramid_request.db

    def test_passes_overrides_parsed_from_get_params(self, pyramid_request):
        pyramid_request.GET["something-else"] = ""
        pyramid_request.GET["__feature__[foo]"] = ""
        pyramid_request.GET["__feature__[bar]"] = ""

        svc = feature_service_factory(None, pyramid_request)

        assert svc.overrides == {"foo": True, "bar": True}

    @pytest.mark.parametrize(
        "feature,client_version,disabled",
        [
            # No or invalid Hypothesis-Client-Version header
            ("pdf_image_annotation", "", False),
            ("pdf_image_annotation", "not-valid", False),
            # Old client version
            ("pdf_image_annotation", "1.1623.0", True),
            # New client version
            ("pdf_image_annotation", "1.1633.0", False),
            ("pdf_image_annotation", "1.1634.0", False),
        ],
    )
    def test_disables_features_in_old_clients(
        self, pyramid_request, feature, client_version, disabled
    ):
        pyramid_request.headers["Hypothesis-Client-Version"] = client_version
        svc = feature_service_factory(None, pyramid_request)
        expected = {feature: False} if disabled else {}

        assert svc.overrides == expected

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.user = mock.sentinel.user
        return pyramid_request
