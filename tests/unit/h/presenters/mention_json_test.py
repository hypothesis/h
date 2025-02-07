import pytest

from h.models import Mention
from h.presenters.mention_json import MentionJSONPresenter
from h.util.user import format_userid


class TestMentionJSONPresenter:
    def test_as_dict(self, user, annotation):
        mention = Mention(annotation=annotation, user=user, username=user.username)

        data = MentionJSONPresenter(mention).asdict()

        assert data == {
            "userid": user.userid,
            "original_userid": user.userid,
            "username": user.username,
            "display_name": user.display_name,
            "link": user.uri,
        }

    def test_as_dict_with_different_username(self, user, annotation):
        new_username = "new_username"
        mention = Mention(annotation=annotation, user=user, username=new_username)

        data = MentionJSONPresenter(mention).asdict()

        assert data["original_userid"] == format_userid(new_username, user.authority)

    @pytest.fixture
    def user(self, factories):
        return factories.User.build()

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation.build()
