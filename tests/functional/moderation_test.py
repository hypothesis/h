import pytest


class TestModeration:
    def test_moderator_flag_listing(
        self, app, flagged_annotation, moderator_with_token
    ):
        _, token = moderator_with_token

        headers = {"Authorization": f"Bearer {token.value}"}
        annotation_url = f"/api/annotations/{flagged_annotation.id}"
        res = app.get(annotation_url, headers=headers)

        assert "moderation" in res.json
        assert res.json["moderation"]["flagCount"] > 0


@pytest.fixture
def group(db_session, factories, moderator):
    group = factories.OpenGroup(creator=moderator)
    db_session.commit()
    return group


@pytest.fixture
def flagged_annotation(group, db_session, factories):
    ann = factories.Annotation(groupid=group.pubid, shared=True)
    factories.Flag(annotation=ann)
    db_session.commit()
    return ann


@pytest.fixture
def moderator(db_session, factories):
    user = factories.User()
    db_session.commit()
    return user


@pytest.fixture
def moderator_with_token(moderator, db_session, factories):
    token = factories.DeveloperToken(user=moderator)
    db_session.commit()
    return (moderator, token)
