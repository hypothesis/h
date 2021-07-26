import pytest

# Permission.Group.ADMIN
# OAuth clients, staff and admins can edit a group
# The creator of thr group can also edit the group


@pytest.mark.usefixtures("with_logged_in_user")
class TestGroupEditController:
    @pytest.mark.xfail  # See https://github.com/hypothesis/product-backlog/issues/109
    def test_group_page_includes_referrer_tag(self, app, db_session, factories, user):
        """
        The group read page should include a referrer tag.

        When a logged-in user who is a member of the group visits the group's page,
        the page should include a `<meta name="referrer" ...` tag that asks the
        browser not to send the path part of the page's URL to third-party servers
        in the Referer header when following links on the page.

        This is because the group's URL is secret - if you have it you can join
        the group.
        """
        group = factories.Group(creator=user)
        db_session.commit()

        res = app.get(
            "/groups/{pubid}/{slug}".format(pubid=group.pubid, slug=group.slug)
        )

        assert res.html.head.find("meta", attrs={"name": "referrer"}, content="origin")

    def test_submit_create_group_form_without_xhr_returns_full_html_page(
        self, filled_out_group_form
    ):
        res = filled_out_group_form.submit().follow()

        assert res.text.startswith("<!DOCTYPE html>")

    def test_submit_create_group_form_with_xhr_returns_partial_html_snippet(
        self, filled_out_group_form
    ):
        res = filled_out_group_form.submit(xhr=True)

        assert res.body.strip(b"\n").startswith(b"<form")
        assert res.content_type == "text/plain"

    @pytest.fixture
    def filled_out_group_form(self, app):
        res = app.get("/groups/new")
        group_form = res.forms["deform"]
        group_form["name"] = "My New Group"

        return group_form
