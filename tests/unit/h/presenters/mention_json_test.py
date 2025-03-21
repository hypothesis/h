import factory
import pytest

from h.models import Mention
from h.presenters.mention_json import MentionJSONPresenter
from h.util.datetime import utc_iso8601
from h.util.user import format_userid


class TestMentionJSONPresenter:
    def test_as_dict(self, user, annotation, pyramid_request):
        mention = Mention(annotation=annotation, user=user, username=user.username)

        data = MentionJSONPresenter(mention, pyramid_request).asdict()

        assert data == {
            "userid": user.userid,
            "original_userid": user.userid,
            "username": user.username,
            "display_name": user.display_name,
            "link": f"http://example.com/users/{user.username}",
            "description": user.description,
            "joined": utc_iso8601(user.activation_date),
        }

    def test_as_dict_with_different_username(self, user, annotation, pyramid_request):
        new_username = "new_username"
        mention = Mention(annotation=annotation, user=user, username=new_username)

        data = MentionJSONPresenter(mention, pyramid_request).asdict()

        assert data["original_userid"] == format_userid(new_username, user.authority)

    @pytest.fixture
    def user(self, factories):
        return factories.User.build(
            description="user description",
            activation_date=factory.Faker("date_time_this_decade"),
        )

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation.build()

    @pytest.fixture(autouse=True)
    def routes(self, pyramid_config):
        pyramid_config.add_route("activity.user_search", "/users/{username}")
