from h.models import GroupMembership, GroupMembershipRoles


class TestModeration:
    def test_it(self, app, db_session, factories):
        group = factories.OpenGroup()
        annotation = factories.Annotation(group=group, shared=True)
        factories.Flag(annotation=annotation)
        moderator = factories.User(
            memberships=[
                GroupMembership(group=group, roles=[GroupMembershipRoles.MODERATOR])
            ]
        )
        token = factories.DeveloperToken(user=moderator)
        db_session.commit()

        response = app.get(
            f"/api/annotations/{annotation.id}",
            headers={"Authorization": f"Bearer {token.value}"},
        )

        assert "moderation" in response.json
        assert response.json["moderation"]["flagCount"] > 0
