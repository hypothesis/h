from datetime import UTC, datetime
from unittest.mock import ANY, create_autospec, sentinel

import pytest
from colander import Invalid
from deform import ValidationFailure

from h import i18n
from h.services.exceptions import ConflictError
from h.views.account_signup import SignupViews, is_authenticated

_ = i18n.TranslationString


@pytest.mark.usefixtures("user_signup_service")
class TestSignupViews:
    def test_get(self, views, get_csrf_token, pyramid_request):
        response = views.get()

        get_csrf_token.assert_called_once_with(pyramid_request)
        assert response == {"js_config": {"csrfToken": get_csrf_token.return_value}}

    @pytest.mark.usefixtures("frozen_time")
    def test_post(
        self,
        views,
        SignupSchema,
        pyramid_request,
        user_signup_service,
        get_csrf_token,
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
        assert response == {
            "js_config": {"csrfToken": get_csrf_token.return_value},
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
        self, views, post_params, expected_form_data, get_csrf_token, pyramid_request
    ):
        views.context = ValidationFailure(
            sentinel.field,
            sentinel.cstruct,
            error=create_autospec(Invalid, instance=True, spec_set=True),
        )
        pyramid_request.POST = post_params

        response = views.validation_failure()

        get_csrf_token.assert_called_once_with(pyramid_request)
        assert response == {
            "js_config": {
                "csrfToken": get_csrf_token.return_value,
                "formErrors": views.context.error.asdict.return_value,
                "formData": expected_form_data,
            }
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


def test_is_authenticated(matchers, pyramid_request, authenticated_user):
    response = is_authenticated(pyramid_request)

    assert response == matchers.Redirect302To(
        pyramid_request.route_url(
            "activity.user_search", username=authenticated_user.username
        )
    )


@pytest.fixture
def authenticated_user(factories, pyramid_config, pyramid_request):
    user = factories.User()
    pyramid_request.user = user
    pyramid_config.testing_securitypolicy(userid=user.userid)
    return user


@pytest.fixture(autouse=True)
def routes(pyramid_config):
    pyramid_config.add_route("activity.user_search", "/users/{username}")


@pytest.fixture(autouse=True)
def get_csrf_token(patch):
    return patch("h.views.account_signup.get_csrf_token")


@pytest.fixture(autouse=True)
def SignupSchema(patch):
    return patch("h.views.account_signup.SignupSchema")
