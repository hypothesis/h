import pytest
from pytest import param


# h.views.activity
class TestGroupSearchController:
    @pytest.mark.usefixtures("with_logged_in_user")
    @pytest.mark.xfail  # See https://github.com/hypothesis/product-backlog/issues/109
    def test_group_page_includes_referrer_tag(self, app, user_owned_group):
        """
        The group read page should include a referrer tag.

        When a logged-in user who is a member of the group visits the group's page,
        the page should include a `<meta name="referrer" ...` tag that asks the
        browser not to send the path part of the page's URL to third-party servers
        in the Referer header when following links on the page.

        This is because the group's URL is secret - if you have it you can join
        the group.
        """

        response = app.get(f"/groups/{user_owned_group.pubid}/{user_owned_group.slug}")

        assert response.html.head.find(
            "meta", attrs={"name": "referrer"}, content="origin"
        )


# h.views.group
class TestGroupCreateController:
    @pytest.mark.usefixtures("with_logged_in_user")
    def test_submit_create_group_form_without_xhr_returns_full_html_page(
        self, filled_out_group_form
    ):
        response = filled_out_group_form.submit().follow()

        assert response.text.startswith("<!DOCTYPE html>")

    @pytest.mark.usefixtures("with_logged_in_user")
    def test_submit_create_group_form_with_xhr_returns_partial_html_snippet(
        self, filled_out_group_form
    ):
        response = filled_out_group_form.submit(xhr=True)

        assert response.body.strip(b"\n").startswith(b"<form")
        assert response.content_type == "text/plain"

    @pytest.fixture
    def filled_out_group_form(self, app):
        response = app.get("/groups/new")
        group_form = response.forms["deform"]
        group_form["name"] = "My New Group"

        return group_form


# h.views.group
class TestGroupEditController:
    # These permissions tests are a stand-in for testing all functionality of
    # the group edit controller as they all need the same permission. We will
    # just test GET as it's the simplest.
    @pytest.mark.usefixtures("with_logged_in_user")
    def test_a_logged_in_user_can_edit_their_own_groups(self, app, user_owned_group):
        app.get(f"/groups/{user_owned_group.pubid}/edit")

    @pytest.mark.parametrize(
        "is_staff,is_admin,expected_status",
        (
            param(True, False, 200, id="staff"),
            param(False, True, 200, id="admin"),
            # Regular users can't edit other people's groups
            param(False, False, 404, id="regular_user"),
        ),
    )
    def test_editing_other_peoples_groups(
        self, app, group, login_user, is_staff, is_admin, expected_status
    ):
        login_user(staff=is_staff, admin=is_admin)

        app.get(f"/groups/{group.pubid}/edit", status=expected_status)

    @pytest.fixture
    def group(self, factories, db_session):
        group = factories.Group()
        db_session.commit()

        return group


@pytest.fixture
def user_owned_group(factories, db_session, user):
    group = factories.Group(creator=user)
    db_session.commit()

    return group
