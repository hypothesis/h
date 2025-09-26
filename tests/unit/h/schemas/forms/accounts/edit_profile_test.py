import colander
import pytest

from h.schemas.forms.accounts import EditProfileSchema

pytestmark = pytest.mark.usefixtures("pyramid_config")


class TestEditProfileSchema:
    def test_accepts_valid_input(self, pyramid_csrf_request):
        schema = EditProfileSchema().bind(request=pyramid_csrf_request)
        schema.deserialize(
            {
                "display_name": "Michael Granitzer",
                "description": "Professor at University of Passau",
                "link": "http://mgrani.github.io/",
                "location": "Bavaria, Germany",
            }
        )

    def test_rejects_invalid_url(self, pyramid_csrf_request, validate_url):
        validate_url.side_effect = ValueError("Invalid URL")
        schema = EditProfileSchema().bind(request=pyramid_csrf_request)
        with pytest.raises(colander.Invalid) as exc:
            schema.deserialize({"link": '"invalid URL"'})
        assert exc.value.asdict()["link"] == "Invalid URL"


@pytest.fixture
def validate_url(patch):
    return patch("h.accounts.util.validate_url")
