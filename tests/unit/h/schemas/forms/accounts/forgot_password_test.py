import colander
import pytest

from h.schemas.forms.accounts import ForgotPasswordSchema

pytestmark = pytest.mark.usefixtures("pyramid_config")


@pytest.mark.usefixtures("user_model")
class TestForgotPasswordSchema:
    def test_it_is_invalid_with_no_user(self, pyramid_csrf_request, user_model):
        schema = ForgotPasswordSchema().bind(request=pyramid_csrf_request)
        user_model.get_by_email.return_value = None

        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"email": "rapha@example.com"})

        assert "email" in exc.value.asdict()
        assert exc.value.asdict()["email"] == "Unknown email address."

    def test_it_returns_user_when_valid(self, pyramid_csrf_request, user_model):
        schema = ForgotPasswordSchema().bind(request=pyramid_csrf_request)
        user = user_model.get_by_email.return_value

        appstruct = schema.deserialize({"email": "rapha@example.com"})

        assert appstruct["user"] == user


@pytest.fixture
def user_model(patch):
    return patch("h.accounts.schemas.models.User")
