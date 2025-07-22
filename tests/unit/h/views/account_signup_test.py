from datetime import UTC, datetime, timedelta
from unittest.mock import ANY, create_autospec, sentinel

import pytest
from colander import Invalid
from deform import ValidationFailure
from pyramid.httpexceptions import HTTPFound

from h import i18n
from h.models.user_identity import IdentityProvider
from h.services.exceptions import ConflictError
from h.services.jwt import JWTDecodeError
from h.views.account_signup import (
    IDInfo,
    IDInfoJWTDecodeError,
    JWTAudiences,
    JWTIssuers,
    ORCIDSignupViews,
    SignupViews,
    is_authenticated,
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

    @pytest.mark.usefixtures("frozen_time")
    def test_post(
        self,
        views,
        SignupSchema,
        pyramid_request,
        user_signup_service,
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
            privacy_accepted=datetime.now(UTC),
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

    def test_post_when_validation_failure(
        self, pyramid_request, views, user_signup_service
    ):
        pyramid_request.create_form.return_value.validate.side_effect = (
            ValidationFailure(sentinel.field, sentinel.cstruct, error=sentinel.error)
        )

        with pytest.raises(ValidationFailure):
            views.post()

        user_signup_service.signup.assert_not_called()

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
        self,
        views,
        post_params,
        expected_form_data,
        get_csrf_token,
        pyramid_request,
        feature_service,
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


@pytest.mark.usefixtures("user_signup_service", "jwt_service", "feature_service")
class TestORCIDSignupViews:
    def test_get(
        self, views, get_csrf_token, pyramid_request, orcid_id, feature_service
    ):
        response = views.get()

        get_csrf_token.assert_called_once_with(pyramid_request)
        feature_service.enabled.assert_called_once_with("log_in_with_orcid", None)
        assert response == {
            "js_config": {
                "csrfToken": get_csrf_token.return_value,
                "features": {"log_in_with_orcid": feature_service.enabled.return_value},
                "identity": {"orcid": {"id": orcid_id}},
            }
        }

    @pytest.mark.parametrize(
        "appstruct,expected_signup_args",
        [
            ({"comms_opt_in": True}, {"comms_opt_in": True}),
            ({"comms_opt_in": False}, {"comms_opt_in": False}),
            ({"comms_opt_in": None}, {"comms_opt_in": False}),
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
        SSOSignupSchema,
    ):
        pyramid_request.create_form.return_value.validate.return_value = {
            "username": sentinel.username,
            **appstruct,
        }

        response = views.post()

        SSOSignupSchema.assert_called_once_with()
        SSOSignupSchema.return_value.bind.assert_called_once_with(
            request=pyramid_request
        )
        pyramid_request.create_form.assert_called_once_with(
            SSOSignupSchema.return_value.bind.return_value
        )
        pyramid_request.create_form.return_value.validate.assert_called_once_with(ANY)
        assert list(
            pyramid_request.create_form.return_value.validate.call_args[0][0]
        ) == list(pyramid_request.POST.items())
        user_signup_service.signup.assert_called_once_with(
            username=sentinel.username,
            email=None,
            password=None,
            privacy_accepted=frozen_time().astimezone(UTC),
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
    def test_when_jwt_is_invalid(self, views, view_method, jwt_service):
        jwt_service.decode_symmetric.side_effect = JWTDecodeError

        with pytest.raises(IDInfoJWTDecodeError):
            getattr(views, view_method)()

    def test_idinfo_jwt_decode_error(self, views, report_exception, pyramid_request):
        response = views.idinfo_jwt_decode_error()

        report_exception.assert_called_once_with(sentinel.context)
        assert pyramid_request.response.status_int == 403
        assert response == {"error": "Decoding idinfo JWT failed."}

    @pytest.mark.parametrize(
        "post_params,expected_form_data",
        [
            # It copies the submitted form fields into the returned form data
            # when re-rendering the page.
            (
                {
                    "username": sentinel.username,
                    "privacy_accepted": "true",
                    "comms_opt_in": "true",
                },
                {
                    "username": sentinel.username,
                    "privacy_accepted": True,
                    "comms_opt_in": True,
                },
            ),
            # If privacy_accepted and comms_opt_in are not "true" in the post
            # params then they're False in the returned form data.
            (
                {
                    "username": sentinel.username,
                    "privacy_accepted": "false",
                    "comms_opt_in": "false",
                },
                {
                    "username": sentinel.username,
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
                    "privacy_accepted": False,
                    "comms_opt_in": False,
                },
            ),
        ],
    )
    def test_validation_failure(
        self,
        views,
        post_params,
        expected_form_data,
        get_csrf_token,
        pyramid_request,
        feature_service,
        jwt_service,
        orcid_id,
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
        jwt_service.encode_symmetric.assert_called_once_with(
            IDInfo(orcid_id),
            expires_in=timedelta(hours=1),
            issuer=JWTIssuers.SIGNUP_VALIDATION_FAILURE_ORCID,
            audience=JWTAudiences.SIGNUP_ORCID,
        )
        assert response == {
            "js_config": {
                "csrfToken": get_csrf_token.return_value,
                "features": {"log_in_with_orcid": feature_service.enabled.return_value},
                "identity": {"orcid": {"id": orcid_id}},
                "formErrors": views.context.error.asdict.return_value,
                "formData": {
                    "idinfo": jwt_service.encode_symmetric.return_value,
                    **expected_form_data,
                },
            }
        }

    @pytest.fixture
    def orcid_id(self):
        return "test_orcid_id"

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params["idinfo"] = sentinel.idinfo
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

    @pytest.fixture
    def jwt_service(self, jwt_service, orcid_id):
        jwt_service.decode_symmetric.return_value = IDInfo(orcid_id)
        return jwt_service


def test_is_authenticated(matchers, pyramid_request, authenticated_user):
    response = is_authenticated(pyramid_request)

    assert response == matchers.Redirect302To(
        pyramid_request.route_url(
            "activity.user_search", username=authenticated_user.username
        )
    )


@pytest.fixture(autouse=True)
def get_csrf_token(patch):
    return patch("h.views.account_signup.get_csrf_token")


@pytest.fixture(autouse=True)
def SignupSchema(patch):
    return patch("h.views.account_signup.SignupSchema")


@pytest.fixture(autouse=True)
def SSOSignupSchema(patch):
    return patch("h.views.account_signup.SSOSignupSchema")


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
def authenticated_user(factories, pyramid_config, pyramid_request):
    user = factories.User()
    pyramid_request.user = user
    pyramid_config.testing_securitypolicy(userid=user.userid)
    return user
