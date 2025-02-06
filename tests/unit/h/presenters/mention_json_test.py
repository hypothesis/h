import pytest

from h.models import Mention
from h.presenters.mention_json import MentionJSONPresenter


class TestMentionJSONPresenter:
    def test_as_dict(self, user, annotation):
        mention = Mention(annotation=annotation, user=user, username=user.username)

        data = MentionJSONPresenter(mention).asdict()

        assert data == {
            "userid": user.userid,
            "username": user.username,
            "display_name": user.display_name,
            "link": user.uri,
        }

    @pytest.fixture
    def user(self, factories):
        return factories.User.build()

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation.build()
