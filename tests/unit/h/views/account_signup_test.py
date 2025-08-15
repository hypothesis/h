from datetime import UTC, datetime, timedelta
from unittest.mock import ANY, call, create_autospec, sentinel

import pytest
from colander import Invalid
from deform import ValidationFailure
from pyramid.httpexceptions import HTTPFound

from h import i18n
from h.models.user_identity import IdentityProvider
from h.services.jwt import JWTAudience, JWTDecodeError
from h.services.user_signup import (
    EmailConflictError,
    IdentityConflictError,
    UsernameConflictError,
)
from h.views.account_signup import (
    IDInfo,
    IDInfoJWTDecodeError,
    SignupViews,
    SocialLoginSignupViews,
    decode_idinfo_token,
    encode_idinfo_token,
    is_authenticated,
)

_ = i18n.TranslationString


@pytest.mark.usefixtures("user_signup_service", "feature_service")
class TestSignupViews:
    def test_get(self, views, get_csrf_token, pyramid_request, feature_service):
        feature_service.enabled.side_effect = [
            sentinel.orcid_enabled,
            sentinel.google_enabled,
            sentinel.facebook_enabled,
        ]

        response = views.get()

        get_csrf_token.assert_called_once_with(pyramid_request)
        assert feature_service.enabled.call_args_list == [
            call("log_in_with_orcid", user=None),
            call("log_in_with_google", user=None),
            call("log_in_with_facebook", user=None),
        ]
        assert response == {
            "js_config": {
                "csrfToken": get_csrf_token.return_value,
                "features": {
                    "log_in_with_orcid": sentinel.orcid_enabled,
                    "log_in_with_google": sentinel.google_enabled,
                    "log_in_with_facebook": sentinel.facebook_enabled,
                },
                "forOAuth": False,
                "form": {},
                "urls": {
                    "login": {
                        "username_or_email": pyramid_request.route_url("login"),
                        **{
                            provider: pyramid_request.route_url(
                                f"oidc.login.{provider}"
                            )
                            for provider in ("facebook", "google", "orcid")
                        },
                    },
                    "signup": pyramid_request.route_url("signup"),
                },
            }
        }

    def test_get_when_feature_flags_disabled(
        self, views, pyramid_request, feature_service
    ):
        feature_service.enabled.return_value = False
        pyramid_request.feature.flags = {
            "log_in_with_facebook": False,
            "log_in_with_google": False,
            "log_in_with_orcid": False,
        }

        response = views.get()

        assert response["js_config"]["features"] == {
            "log_in_with_facebook": False,
            "log_in_with_google": False,
            "log_in_with_orcid": False,
        }
        for provider in ("facebook", "google", "orcid"):
            assert provider not in response["js_config"].get("urls", {}).get(
                "login", {}
            )

    def test_get_copies_next_query_param_onto_social_login_urls(
        self, views, pyramid_request
    ):
        pyramid_request.params["next"] = "http://example.com/oauth/authorize"

        response = views.get()

        assert response["js_config"]["urls"]["login"] == {
            "username_or_email": pyramid_request.route_url(
                "login", _query={"next": "http://example.com/oauth/authorize"}
            ),
            **{
                provider: pyramid_request.route_url(
                    f"oidc.login.{provider}",
                    _query={"next": "http://example.com/oauth/authorize"},
                )
                for provider in ("facebook", "google", "orcid")
            },
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
        feature_service.enabled.side_effect = [
            sentinel.orcid_enabled,
            sentinel.google_enabled,
            sentinel.facebook_enabled,
        ]

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
        assert feature_service.enabled.call_args_list == [
            call("log_in_with_orcid", user=None),
            call("log_in_with_google", user=None),
            call("log_in_with_facebook", user=None),
        ]
        assert response == {
            "js_config": {
                "csrfToken": get_csrf_token.return_value,
                "features": {
                    "log_in_with_orcid": sentinel.orcid_enabled,
                    "log_in_with_google": sentinel.google_enabled,
                    "log_in_with_facebook": sentinel.facebook_enabled,
                },
                "forOAuth": False,
                "form": {},
                "urls": {
                    "login": {
                        "username_or_email": pyramid_request.route_url("login"),
                        "facebook": pyramid_request.route_url("oidc.login.facebook"),
                        "google": pyramid_request.route_url("oidc.login.google"),
                        "orcid": pyramid_request.route_url("oidc.login.orcid"),
                    },
                    "signup": pyramid_request.route_url("signup"),
                },
            },
            "heading": _("Account registration successful"),
        }

    def test_post_when_feature_flags_disabled(
        self, views, pyramid_request, feature_service
    ):
        feature_service.enabled.return_value = False
        pyramid_request.feature.flags = {
            "log_in_with_facebook": False,
            "log_in_with_google": False,
            "log_in_with_orcid": False,
        }

        response = views.post()

        assert response["js_config"]["features"] == {
            "log_in_with_orcid": False,
            "log_in_with_google": False,
            "log_in_with_facebook": False,
        }
        for provider in ("facebook", "google", "orcid"):
            assert provider not in response["js_config"].get("urls", {}).get(
                "login", {}
            )

    def test_post_copies_next_query_param_onto_social_login_urls(
        self, pyramid_request, views
    ):
        pyramid_request.params["next"] = "http://example.com/oauth/authorize"

        response = views.post()

        assert response["js_config"]["urls"]["login"] == {
            "username_or_email": pyramid_request.route_url(
                "login", _query={"next": "http://example.com/oauth/authorize"}
            ),
            **{
                provider: pyramid_request.route_url(
                    f"oidc.login.{provider}",
                    _query={"next": "http://example.com/oauth/authorize"},
                )
                for provider in ("facebook", "google", "orcid")
            },
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
        feature_service.enabled.side_effect = [
            sentinel.orcid_enabled,
            sentinel.google_enabled,
            sentinel.facebook_enabled,
        ]
        views.context = ValidationFailure(
            sentinel.field,
            sentinel.cstruct,
            error=create_autospec(Invalid, instance=True, spec_set=True),
        )
        pyramid_request.POST = post_params

        response = views.validation_failure()

        get_csrf_token.assert_called_once_with(pyramid_request)
        assert feature_service.enabled.call_args_list == [
            call("log_in_with_orcid", user=None),
            call("log_in_with_google", user=None),
            call("log_in_with_facebook", user=None),
        ]
        assert response == {
            "js_config": {
                "csrfToken": get_csrf_token.return_value,
                "form": {
                    "data": expected_form_data,
                    "errors": views.context.error.asdict.return_value,
                },
                "features": {
                    "log_in_with_orcid": sentinel.orcid_enabled,
                    "log_in_with_google": sentinel.google_enabled,
                    "log_in_with_facebook": sentinel.facebook_enabled,
                },
                "forOAuth": False,
                "urls": {
                    "login": {
                        "username_or_email": pyramid_request.route_url("login"),
                        "facebook": pyramid_request.route_url("oidc.login.facebook"),
                        "google": pyramid_request.route_url("oidc.login.google"),
                        "orcid": pyramid_request.route_url("oidc.login.orcid"),
                    },
                    "signup": pyramid_request.route_url("signup"),
                },
            }
        }

    def test_validation_failure_when_feature_flags_disabled(
        self,
        views,
        pyramid_request,
        feature_service,
    ):
        feature_service.enabled.return_value = False
        pyramid_request.feature.flags = {
            "log_in_with_facebook": False,
            "log_in_with_google": False,
            "log_in_with_orcid": False,
        }
        views.context = ValidationFailure(
            sentinel.field,
            sentinel.cstruct,
            error=create_autospec(Invalid, instance=True, spec_set=True),
        )

        response = views.validation_failure()

        assert response["js_config"]["features"] == {
            "log_in_with_orcid": False,
            "log_in_with_google": False,
            "log_in_with_facebook": False,
        }
        for provider in ("facebook", "google", "orcid"):
            assert provider not in response["js_config"].get("urls", {}).get(
                "login", {}
            )

    def test_validation_failure_copies_next_query_param_onto_social_login_urls(
        self, pyramid_request, views
    ):
        pyramid_request.params["next"] = "http://example.com/oauth/authorize"
        views.context = ValidationFailure(
            sentinel.field,
            sentinel.cstruct,
            error=create_autospec(Invalid, instance=True, spec_set=True),
        )

        response = views.validation_failure()

        assert response["js_config"]["urls"]["login"] == {
            "username_or_email": pyramid_request.route_url(
                "login", _query={"next": "http://example.com/oauth/authorize"}
            ),
            **{
                provider: pyramid_request.route_url(
                    f"oidc.login.{provider}",
                    _query={"next": "http://example.com/oauth/authorize"},
                )
                for provider in ("facebook", "google", "orcid")
            },
        }

    @pytest.mark.parametrize(
        "exception_class,errors",
        [
            (UsernameConflictError, {"username": "This username is already taken."}),
            (EmailConflictError, {"email": "This email address is already taken."}),
        ],
    )
    def test_validation_failure_with_conflict_error(
        self, views, exception_class, errors
    ):
        views.context = exception_class()

        response = views.validation_failure()

        assert response["js_config"]["form"]["errors"] == errors

    @pytest.mark.parametrize(
        "exception_class", [UsernameConflictError, EmailConflictError]
    )
    def test_post_when_signup_conflict(
        self, user_signup_service, views, exception_class
    ):
        user_signup_service.signup.side_effect = exception_class

        with pytest.raises(exception_class):
            views.post()

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


class TestIDInfo:
    @pytest.mark.parametrize(
        "name,given_name,family_name,display_name",
        [
            # By default `display_name` is `None`.
            (None, None, None, None),
            # If present `name` is used for `display_name`.
            ("Vannevar Bush", None, None, "Vannevar Bush"),
            # `name` overrides `given_name` and `family_name`.
            ("Vannevar Bush", "given_name", "family_name", "Vannevar Bush"),
            # If there's no name then "{given_name} {family_name}" is used for display_name.
            (None, "Vannevar", "Bush", "Vannevar Bush"),
            # If there's a given_name but no name or family_name then given_name is used for display_name.
            (None, "Vannevar", None, "Vannevar"),
        ],
    )
    def test_display_name(self, name, given_name, family_name, display_name):
        idinfo = IDInfo(
            sub=sentinel.sub,
            name=name,
            given_name=given_name,
            family_name=family_name,
        )

        assert idinfo.display_name == display_name


@pytest.mark.usefixtures(
    "user_service", "user_signup_service", "jwt_service", "feature_service"
)
class TestSocialLoginSignupViews:
    def test_get(
        self,
        views,
        get_csrf_token,
        pyramid_request,
        orcid_id,
        feature_service,
        jwt_service,
    ):
        feature_service.enabled.side_effect = [
            sentinel.orcid_enabled,
            sentinel.google_enabled,
            sentinel.facebook_enabled,
        ]

        response = views.get()

        jwt_service.decode_symmetric.assert_called_once_with(
            sentinel.idinfo,
            audience=JWTAudience.SIGNUP_ORCID,
            payload_class=IDInfo,
        )
        get_csrf_token.assert_called_once_with(pyramid_request)
        assert feature_service.enabled.call_args_list == [
            call("log_in_with_orcid", user=None),
            call("log_in_with_google", user=None),
            call("log_in_with_facebook", user=None),
        ]
        assert response == {
            "js_config": {
                "csrfToken": get_csrf_token.return_value,
                "features": {
                    "log_in_with_orcid": sentinel.orcid_enabled,
                    "log_in_with_google": sentinel.google_enabled,
                    "log_in_with_facebook": sentinel.facebook_enabled,
                },
                "form": {},
                "identity": {"provider_unique_id": orcid_id, "email": None},
            }
        }

    def test_get_when_theres_an_identity_conflict(self, views, user_service, idinfo):
        user_service.fetch_by_identity.return_value = sentinel.conflicting_user

        with pytest.raises(IdentityConflictError):
            views.get()

        user_service.fetch_by_identity.assert_called_once_with(
            IdentityProvider.ORCID, idinfo.sub
        )

    def test_get_when_theres_an_email_conflict(self, views, factories, idinfo):
        conflicting_user = factories.User()
        idinfo.email = conflicting_user.email

        with pytest.raises(EmailConflictError):
            views.get()

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
        SocialLoginSignupSchema,
    ):
        pyramid_request.create_form.return_value.validate.return_value = {
            "username": sentinel.username,
            **appstruct,
        }

        response = views.post()

        SocialLoginSignupSchema.assert_called_once_with()
        SocialLoginSignupSchema.return_value.bind.assert_called_once_with(
            request=pyramid_request
        )
        pyramid_request.create_form.assert_called_once_with(
            SocialLoginSignupSchema.return_value.bind.return_value
        )
        pyramid_request.create_form.return_value.validate.assert_called_once_with(ANY)
        assert list(
            pyramid_request.create_form.return_value.validate.call_args[0][0]
        ) == list(pyramid_request.POST.items())
        user_signup_service.signup.assert_called_once_with(
            username=sentinel.username,
            email=None,
            display_name=None,
            password=None,
            privacy_accepted=frozen_time().astimezone(UTC),
            require_activation=False,
            identities=[
                {
                    "provider": IdentityProvider.ORCID,
                    "provider_unique_id": orcid_id,
                    "email": None,
                    "name": None,
                    "given_name": None,
                    "family_name": None,
                }
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

    def test_post_when_next_url_in_idinfo_token(
        self, views, idinfo, pyramid_request, matchers
    ):
        pyramid_request.create_form.return_value.validate.return_value = {
            "username": sentinel.username
        }
        idinfo.next_url = "http://example.com/oauth/authorize"

        response = views.post()

        assert response == matchers.Redirect302To("http://example.com/oauth/authorize")

    @pytest.mark.parametrize(
        "next_url", [None, "http://example.com/unknown", "https://evil.com"]
    )
    def test_post_when_next_url_missing_or_unknown(
        self,
        views,
        idinfo,
        pyramid_request,
        matchers,
        next_url,
        user_signup_service,
    ):
        pyramid_request.create_form.return_value.validate.return_value = {
            "username": sentinel.username
        }
        idinfo.next_url = next_url

        response = views.post()

        assert response == matchers.Redirect302To(
            pyramid_request.route_url(
                "activity.user_search",
                username=user_signup_service.signup.return_value.username,
            )
        )

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

    @pytest.mark.parametrize(
        "route_name,provider",
        [
            ("signup.orcid", "ORCID"),
            ("signup.google", "Google"),
            ("signup.facebook", "Facebook"),
        ],
    )
    def test_email_conflict_error(
        self, views, route_name, provider, pyramid_request, matchers, idinfo, logout
    ):
        pyramid_request.matched_route.name = route_name
        idinfo.email = sentinel.email

        response = views.email_conflict_error()

        assert pyramid_request.session.peek_flash("error") == [
            f"There's already a Hypothesis account with your {provider} email address."
            " Try logging in or resetting your password."
            f" Once logged in you can connect {provider} in your account settings.",
        ]
        assert (
            matchers.Redirect302To(
                pyramid_request.route_url("login", _query={"username": idinfo.email})
            )
            == response
        )
        logout.assert_called_once_with(pyramid_request)
        for header in logout.return_value:
            assert header in response.headers.items()

    @pytest.mark.parametrize(
        "route_name,provider",
        [
            ("signup.orcid", "ORCID"),
            ("signup.google", "Google"),
            ("signup.facebook", "Facebook"),
        ],
    )
    def test_identity_conflict_error(
        self, views, route_name, provider, pyramid_request, matchers, logout
    ):
        pyramid_request.matched_route.name = route_name

        response = views.identity_conflict_error()

        assert pyramid_request.session.peek_flash("error") == [
            f"There's already a Hypothesis account connected to your {provider} account. Try logging in.",
        ]
        assert matchers.Redirect302To(pyramid_request.route_url("login")) == response
        logout.assert_called_once_with(pyramid_request)
        for header in logout.return_value:
            assert header in response.headers.items()

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
        orcid_id,
    ):
        views.context = ValidationFailure(
            sentinel.field,
            sentinel.cstruct,
            error=create_autospec(Invalid, instance=True, spec_set=True),
        )
        pyramid_request.POST = post_params
        feature_service.enabled.side_effect = [
            sentinel.orcid_enabled,
            sentinel.google_enabled,
            sentinel.facebook_enabled,
        ]

        response = views.validation_failure()

        get_csrf_token.assert_called_once_with(pyramid_request)
        assert feature_service.enabled.call_args_list == [
            call("log_in_with_orcid", user=None),
            call("log_in_with_google", user=None),
            call("log_in_with_facebook", user=None),
        ]
        assert response == {
            "js_config": {
                "csrfToken": get_csrf_token.return_value,
                "features": {
                    "log_in_with_orcid": sentinel.orcid_enabled,
                    "log_in_with_google": sentinel.google_enabled,
                    "log_in_with_facebook": sentinel.facebook_enabled,
                },
                "identity": {"provider_unique_id": orcid_id, "email": None},
                "form": {
                    "data": expected_form_data,
                    "errors": views.context.error.asdict.return_value,
                },
            }
        }

    def test_validation_failure_with_username_conflict_error(self, views):
        views.context = UsernameConflictError()

        response = views.validation_failure()

        assert response["js_config"]["form"]["errors"] == {
            "username": "This username is already taken."
        }

    @pytest.fixture
    def orcid_id(self):
        return "test_orcid_id"

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.params["idinfo"] = sentinel.idinfo
        pyramid_request.matched_route.name = "signup.orcid"
        return pyramid_request

    @pytest.fixture
    def user_service(self, user_service):
        user_service.fetch_by_identity.return_value = None
        return user_service

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
        return SocialLoginSignupViews(sentinel.context, pyramid_request)

    @pytest.fixture
    def idinfo(self, orcid_id):
        return IDInfo(orcid_id, sentinel.rfp)

    @pytest.fixture
    def jwt_service(self, jwt_service, idinfo):
        jwt_service.decode_symmetric.return_value = idinfo
        return jwt_service


def test_is_authenticated(matchers, pyramid_request, authenticated_user):
    response = is_authenticated(pyramid_request)

    assert response == matchers.Redirect302To(
        pyramid_request.route_url(
            "activity.user_search", username=authenticated_user.username
        )
    )


def test_encode_idinfo_token(jwt_service, matchers, pyramid_request):
    token = encode_idinfo_token(
        jwt_service,
        sentinel.provider_unique_id,
        sentinel.email,
        sentinel.name,
        sentinel.given_name,
        sentinel.family_name,
        sentinel.issuer,
        sentinel.audience,
        sentinel.next_url,
        pyramid_request.session,
    )

    jwt_service.encode_symmetric.assert_called_once_with(
        IDInfo(
            sentinel.provider_unique_id,
            matchers.InstanceOf(str),
            sentinel.email,
            sentinel.name,
            sentinel.given_name,
            sentinel.family_name,
            sentinel.next_url,
        ),
        expires_in=timedelta(hours=1),
        issuer=sentinel.issuer,
        audience=sentinel.audience,
    )
    assert token == {"idinfo": jwt_service.encode_symmetric.return_value}


def test_decode_idinfo_token_valid(jwt_service):
    result = decode_idinfo_token(
        jwt_service, sentinel.idinfo_token, sentinel.audience, sentinel.session
    )

    jwt_service.decode_symmetric.assert_called_once_with(
        sentinel.idinfo_token, audience=sentinel.audience, payload_class=IDInfo
    )
    assert result == jwt_service.decode_symmetric.return_value


def test_decode_idinfo_token_invalid(jwt_service):
    exception = jwt_service.decode_symmetric.side_effect = JWTDecodeError()

    with pytest.raises(IDInfoJWTDecodeError) as exc_info:
        decode_idinfo_token(
            jwt_service, sentinel.idinfo_token, sentinel.audience, sentinel.session
        )

    assert exc_info.value.__cause__ == exception


@pytest.fixture(autouse=True)
def get_csrf_token(patch):
    return patch("h.views.account_signup.get_csrf_token")


@pytest.fixture(autouse=True)
def SignupSchema(patch):
    return patch("h.views.account_signup.SignupSchema")


@pytest.fixture(autouse=True)
def SocialLoginSignupSchema(patch):
    return patch("h.views.account_signup.SocialLoginSignupSchema")


@pytest.fixture(autouse=True)
def login(patch):
    return patch("h.views.account_signup.login")


@pytest.fixture(autouse=True)
def report_exception(patch):
    return patch("h.views.account_signup.report_exception")


@pytest.fixture(autouse=True)
def logout(patch):
    logout = patch("h.views.account_signup.logout")
    logout.return_value = [
        ("logout_headername1", "logout_headervalue1"),
        ("logout_headername2", "logout_headervalue2"),
    ]
    return logout


@pytest.fixture(autouse=True)
def routes(pyramid_config):
    pyramid_config.add_route("activity.user_search", "/users/{username}")
    pyramid_config.add_route("login", "/login")
    pyramid_config.add_route("signup", "/signup")
    pyramid_config.add_route("forgot_password", "/forgot-password")
    pyramid_config.add_route("oauth_authorize", "/oauth/authorize")
    pyramid_config.add_route("oidc.login.facebook", "/oidc/login/facebook")
    pyramid_config.add_route("oidc.login.google", "/oidc/login/google")
    pyramid_config.add_route("oidc.login.orcid", "/oidc/login/orcid")


@pytest.fixture
def authenticated_user(factories, pyramid_config, pyramid_request):
    user = factories.User()
    pyramid_request.user = user
    pyramid_config.testing_securitypolicy(userid=user.userid)
    return user
