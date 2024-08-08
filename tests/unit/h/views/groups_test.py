import pytest
from pyramid.httpexceptions import HTTPMovedPermanently

from h.traversal.group import GroupContext
from h.views import groups as views


class TestGroupCreateController:
    def test_get(self, controller):
        result = controller.get()

        assert result == {}

    @pytest.fixture
    def controller(self, pyramid_request):
        return views.GroupCreateController(pyramid_request)


@pytest.mark.usefixtures("routes")
class TestGroupEditController:
    def test_get_reads_group_properties(self, pyramid_request, group):
        pyramid_request.create_form.return_value = FakeForm()

        result = views.GroupEditController(GroupContext(group), pyramid_request).get()

        assert result == {
            "form": {
                "name": group.name,
                "description": group.description,
            },
            "group_path": f"/g/{group.pubid}/{group.slug}",
        }

    def test_post_sets_group_properties(
        self, form_validating_to, pyramid_request, group
    ):
        controller = views.GroupEditController(GroupContext(group), pyramid_request)
        controller.form = form_validating_to(
            {"name": "New name", "description": "New description"}
        )
        controller.post()

        assert group.name == "New name"
        assert group.description == "New description"

    @pytest.fixture
    def group(self, factories):
        return factories.Group(description="DESCRIPTION")


@pytest.mark.usefixtures("routes")
def test_read_noslug_redirects(pyramid_request, factories):
    group = factories.Group()

    with pytest.raises(HTTPMovedPermanently) as exc:
        views.read_noslug(GroupContext(group), pyramid_request)

    assert exc.value.location == f"/g/{group.pubid}/{group.slug}"


class FakeForm:
    def set_appstruct(self, appstruct):
        self.appstruct = appstruct  # pylint:disable=attribute-defined-outside-init

    def render(self):
        return self.appstruct


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("group_read", "/g/{pubid}/{slug}")
