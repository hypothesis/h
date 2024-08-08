import pytest
from pytest import param

pytestmark = pytest.mark.usefixtures("init_elasticsearch")


class TestGroupEditController:
    # These permissions tests are a stand-in for testing all functionality of
    # the group edit controller as they all need the same permission. We will
    # just test GET as it's the simplest.
    @pytest.mark.usefixtures("with_logged_in_user")
    def test_a_logged_in_user_can_edit_their_own_groups(self, app, user_owned_group):
        app.get(f"/groups/{user_owned_group.pubid}/edit")

    @pytest.mark.parametrize(
        "is_staff,is_admin",
        (
            # Doesn't matter if you are staff or an admin, you can't edit
            # peoples groups using the user facing form
            param(True, False, id="staff"),
            param(False, True, id="admin"),
            param(False, False, id="regular_user"),
        ),
    )
    def test_you_cannot_edit_other_peoples_groups(
        self, app, group, login_user, is_staff, is_admin
    ):
        login_user(staff=is_staff, admin=is_admin)

        app.get(f"/groups/{group.pubid}/edit", status=404)

    @pytest.fixture
    def group(self, factories, db_session):
        group = factories.Group()
        db_session.commit()

        return group
