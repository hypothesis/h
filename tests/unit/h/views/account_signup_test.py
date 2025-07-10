from datetime import UTC
from unittest.mock import ANY, create_autospec, sentinel

import jwt
import pytest
from colander import Invalid
from deform import ValidationFailure
from freezegun import freeze_time
from pyramid.httpexceptions import HTTPFound

from h import i18n
from h.models.user_identity import IdentityProvider
from h.services.exceptions import ConflictError
from h.views.account_signup import (
    AuthJWTDecodeError,
    InvalidAuthJWTPayloadError,
    ORCIDSignupViews,
    SignupViews,
)

_ = i18n.TranslationString


@pytest.mark.usefixtures("user_signup_service", "feature_service")
class TestSignupViews:
    def test_get(self, views, get_csrf_token, pyramid_request, feature_service):
        response = views.get()

        get_csrf_token.assert_called_once_with(pyramid_request)
        feature_service.enabled.assert_called_once_with("log_in_with_orcid", user=None)
        assert response == {
            "js_config": {
                "csrfToken": get_csrf_token.return_value,
                "features": {"log_in_with_orcid": feature_service.enabled.return_value},
            }
        }

    def test_get_redirects_if_logged_in(
        self, pyramid_request, views, authenticated_user
    ):
        with pytest.raises(HTTPFound) as exc_info:
            views.get()

        assert exc_info.value.location == pyramid_request.route_url(
            "activity.user_search", username=authenticated_user.username
        )

    def test_post(
        self,
        views,
        SignupSchema,
        pyramid_request,
        user_signup_service,
        frozen_time,
        get_csrf_token,
        feature_service,
    ):
        response = views.post()

        SignupSchema.assert_called_once_with()
        SignupSchema.return_value.bind.assert_called_once_with(request=pyramid_request)
        pyramid_request.create_form.assert_called_once_with(
            SignupSchema.return_value.bind.return_value
        )
        pyramid_request.create_form.return_value.validate.assert_called_once_with(ANY)
        assert list(
            pyramid_request.create_form.return_value.validate.call_args[0][0]
        ) == list(pyramid_request.POST.items())
        user_signup_service.signup.assert_called_once_with(
            username=sentinel.username,
            email=sentinel.email,
            password=sentinel.password,
            privacy_accepted=frozen_time.astimezone(UTC),
            comms_opt_in=sentinel.comms_opt_in,
        )
        get_csrf_token.assert_called_once_with(pyramid_request)
        feature_service.enabled.assert_called_once_with("log_in_with_orcid", user=None)
        assert response == {
            "js_config": {
                "csrfToken": get_csrf_token.return_value,
                "features": {"log_in_with_orcid": feature_service.enabled.return_value},
            },
            "heading": _("Account registration successful"),
            "message": None,
        }

    def test_post_redirects_if_logged_in(
        self, pyramid_request, views, user_signup_service, authenticated_user
    ):
        with pytest.raises(HTTPFound) as exc_info:
            views.post()

        assert exc_info.value.location == pyramid_request.route_url(
            "activity.user_search", username=authenticated_user.username
        )
        user_signup_service.signup.assert_not_called()

    def test_post_when_validation_failure(
        self, pyramid_request, views, user_signup_service
    ):
        pyramid_request.create_form.return_value.validate.side_effect = (
            ValidationFailure(sentinel.field, sentinel.cstruct, error=sentinel.error)
        )

        with pytest.raises(ValidationFailure):
            views.post()

        user_signup_service.signup.assert_not_called()

    def test_post_when_signup_conflict(
        self, user_signup_service, get_csrf_token, views, pyramid_request
    ):
        user_signup_service.signup.side_effect = ConflictError("Test error message")

        response = views.post()

        get_csrf_token.assert_called_once_with(pyramid_request)
        assert response == {
            "js_config": {"csrfToken": get_csrf_token.return_value},
            "heading": _("Account already registered"),
            "message": _("Test error message"),
        }

    @pytest.mark.parametrize(
        "post_params,expected_form_data",
        [
            # It copies the submitted form fields into the returned form data
            # when re-rendering the page.
            (
                {
                    "username": sentinel.username,
                    "email": sentinel.email,
                    "password": sentinel.password,
                    "privacy_accepted": "true",
                    "comms_opt_in": "true",
                },
                {
                    "username": sentinel.username,
                    "email": sentinel.email,
                    "password": sentinel.password,
                    "privacy_accepted": True,
                    "comms_opt_in": True,
                },
            ),
            # If privacy_accepted and comms_opt_in are not "true" in the post
            # params then they're False in the returned form data.
            (
                {
                    "username": sentinel.username,
                    "email": sentinel.email,
                    "password": sentinel.password,
                    "privacy_accepted": "false",
                    "comms_opt_in": "false",
                },
                {
                    "username": sentinel.username,
                    "email": sentinel.email,
                    "password": sentinel.password,
                    "privacy_accepted": False,
                    "comms_opt_in": False,
                },
            ),
            # If post params are missing from the request the returned form
            # data is empty.
            (
                {},
                {
                    "username": "",
                    "email": "",
                    "password": "",
                    "privacy_accepted": False,
                    "comms_opt_in": False,
                },
            ),
        ],
    )
    def test_validation_failure(
        self, views, post_params, expected_form_data, get_csrf_token, pyramid_request, feature_service
    ):
        views.context = ValidationFailure(
            sentinel.field,
            sentinel.cstruct,
            error=create_autospec(Invalid, instance=True, spec_set=True),
        )
        pyramid_request.POST = post_params

        response = views.validation_failure()

        get_csrf_token.assert_called_once_with(pyramid_request)
        feature_service.enabled.assert_called_once_with("log_in_with_orcid", user=None)
        assert response == {
            "js_config": {
                "csrfToken": get_csrf_token.return_value,
                "formErrors": views.context.error.asdict.return_value,
                "formData": expected_form_data,
                "features": {"log_in_with_orcid": feature_service.enabled.return_value},
            }
        }

    def test_post_when_signup_conflict(
        self,
        user_signup_service,
        get_csrf_token,
        views,
        pyramid_request,
        feature_service,
    ):
        user_signup_service.signup.side_effect = ConflictError("Test error message")

        response = views.post()

        get_csrf_token.assert_called_once_with(pyramid_request)
        feature_service.enabled.assert_called_once_with("log_in_with_orcid", user=None)
        assert response == {
            "js_config": {
                "csrfToken": get_csrf_token.return_value,
                "features": {"log_in_with_orcid": feature_service.enabled.return_value},
            },
            "heading": _("Account already registered"),
            "message": _("Test error message"),
        }

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.create_form.return_value.validate.return_value = {
            "username": sentinel.username,
            "email": sentinel.email,
            "password": sentinel.password,
            "comms_opt_in": sentinel.comms_opt_in,
        }
        return pyramid_request

    @pytest.fixture
    def views(self, pyramid_request):
        return SignupViews(sentinel.context, pyramid_request)

    @pytest.fixture
    def authenticated_user(self, factories, pyramid_config, pyramid_request):
        user = factories.User()
        pyramid_request.user = user
        pyramid_config.testing_securitypolicy(userid=user.userid)
        return user


@pytest.mark.usefixtures("user_signup_service")
class TestORCIDSignupViews:
    def test_get(self, views, get_csrf_token, pyramid_request, orcid_id):
        response = views.get()

        get_csrf_token.assert_called_once_with(pyramid_request)
        assert response == {
            "js_config": {
                "csrfToken": get_csrf_token.return_value,
                "identity": {"orcid.org": {"id": orcid_id}},
            }
        }

    @pytest.mark.parametrize(
        "appstruct,expected_signup_args",
        [
            ({"comms_opt_in": "yes"}, {"comms_opt_in": True}),
            ({"comms_opt_in": "no"}, {"comms_opt_in": False}),
            ({}, {"comms_opt_in": False}),
        ],
    )
    def test_post(
        self,
        views,
        user_signup_service,
        frozen_time,
        orcid_id,
        pyramid_request,
        login,
        appstruct,
        expected_signup_args,
        ORCIDSignupSchema,
    ):
        pyramid_request.create_form.return_value.validate.return_value = {
            "username": sentinel.username,
            **appstruct,
        }

        response = views.post()

        ORCIDSignupSchema.assert_called_once_with()
        ORCIDSignupSchema.return_value.bind.assert_called_once_with(
            request=pyramid_request
        )
        pyramid_request.create_form.assert_called_once_with(
            ORCIDSignupSchema.return_value.bind.return_value
        )
        pyramid_request.create_form.return_value.validate.assert_called_once_with(ANY)
        assert list(
            pyramid_request.create_form.return_value.validate.call_args[0][0]
        ) == list(pyramid_request.POST.items())
        user_signup_service.signup.assert_called_once_with(
            username=sentinel.username,
            email=None,
            password=None,
            privacy_accepted=frozen_time.astimezone(UTC),
            require_activation=False,
            identities=[
                {"provider": IdentityProvider.ORCID, "provider_unique_id": orcid_id}
            ],
            **expected_signup_args,
        )
        assert isinstance(response, HTTPFound)
        assert response.location == pyramid_request.route_url(
            "activity.user_search",
            username=user_signup_service.signup.return_value.username,
        )
        login.assert_called_once_with(
            user_signup_service.signup.return_value, pyramid_request
        )
        for header in login.return_value:
            assert header in response.headerlist

    def test_post_when_form_submission_invalid(self, pyramid_request, views):
        pyramid_request.create_form.return_value.validate.side_effect = (
            ValidationFailure(
                sentinel.field,
                sentinel.cstruct,
                error=create_autospec(Invalid, instance=True, spec_set=True),
            )
        )

        with pytest.raises(ValidationFailure):
            views.post()

    @pytest.mark.parametrize("view_method", ["get", "post"])
    def test_when_jwt_is_invalid(self, views, pyramid_request, view_method):
        pyramid_request.params["auth"] = "invalid"

        with pytest.raises(AuthJWTDecodeError):
            getattr(views, view_method)()

    @pytest.mark.parametrize(
        "payload",
        [
            {"invalid": True},
            {"identity": {"foo": {"id": "bar"}}},
            {"identity": {"orcid.org": {"id": 42}}},
            {"identity": {"orcid.org": {"id": ""}}},
        ],
    )
    @pytest.mark.parametrize("view_method", ["get", "post"])
    def test_when_jwt_payload_is_invalid(
        self, views, payload, authjwt_signing_key, pyramid_request, view_method
    ):
        pyramid_request.params["auth"] = jwt.encode(
            payload, authjwt_signing_key, algorithm="HS256"
        )

        with pytest.raises(InvalidAuthJWTPayloadError):
            getattr(views, view_method)()

    # Username already taken, can delete.
    # Username already taken, cannot delete.
    # Email already taken, can delete.
    # Email already taken, cannot delete.
    # Connected account already exists.
    # make sure it has CSRF protection
    # add expirty to JWT
    # bind JWT to session
    # on form validation error generate a new auth jwt

    @pytest.fixture
    def orcid_id(self):
        return "test_orcid_id"

    @pytest.fixture
    def authjwt_signing_key(self):
        return "test_authjwt_signing_key"

    @pytest.fixture
    def authjwt(self, orcid_id, authjwt_signing_key):
        return jwt.encode(
            {"identity": {"orcid.org": {"id": orcid_id}}},
            authjwt_signing_key,
            algorithm="HS256",
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request, authjwt_signing_key, authjwt):
        pyramid_request.registry.settings.update(
            {"orcid_oidc_authjwt_signing_key": authjwt_signing_key}
        )
        pyramid_request.params["auth"] = authjwt
        return pyramid_request

    @pytest.fixture
    def user_signup_service(self, user_signup_service, factories):
        user_signup_service.signup.return_value = factories.User()
        return user_signup_service

    @pytest.fixture
    def login(self, login):
        login.return_value = [
            ("headername1", "headervalue1"),
            ("headername2", "headervalue2"),
        ]
        return login

    @pytest.fixture
    def views(self, pyramid_request):
        return ORCIDSignupViews(sentinel.context, pyramid_request)


@pytest.fixture(autouse=True)
def get_csrf_token(patch):
    return patch("h.views.account_signup.get_csrf_token")


@pytest.fixture(autouse=True)
def SignupSchema(patch):
    return patch("h.views.account_signup.SignupSchema")


@pytest.fixture(autouse=True)
def ORCIDSignupSchema(patch):
    return patch("h.views.account_signup.ORCIDSignupSchema")


@pytest.fixture(autouse=True)
def login(patch):
    return patch("h.views.account_signup.login")


@pytest.fixture(autouse=True)
def report_exception(patch):
    return patch("h.views.account_signup.report_exception")


@pytest.fixture(autouse=True)
def routes(pyramid_config):
    pyramid_config.add_route("activity.user_search", "/users/{username}")


@pytest.fixture
def frozen_time():
    with freeze_time("2012-01-14 03:21:34") as frozen_time_factory:
        yield frozen_time_factory()
