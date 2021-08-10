from unittest import mock

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPMovedPermanently

from h.traversal.group import GroupContext
from h.views import groups as views


@pytest.mark.usefixtures("group_create_service", "handle_form_submission", "routes")
class TestGroupCreateController:
    def test_get_renders_form(self, controller):
        controller.form = form_validating_to({})

        result = controller.get()

        assert result == {"form": "valid form"}

    def test_post_calls_handle_form_submission(
        self, controller, handle_form_submission
    ):
        controller.post()

        handle_form_submission.assert_called_once_with(
            controller.request, controller.form, Any.function(), Any.function()
        )

    def test_post_returns_handle_form_submission(
        self, controller, handle_form_submission
    ):
        assert controller.post() == handle_form_submission.return_value

    def test_post_creates_new_group_if_form_valid(
        self, controller, group_create_service, handle_form_submission, pyramid_config
    ):
        pyramid_config.testing_securitypolicy("ariadna")

        # If the form submission is valid then handle_form_submission() should
        # call on_success() with the appstruct.
        def call_on_success(  # pylint: disable=unused-argument
            request, form, on_success, on_failure
        ):
            on_success({"name": "my_new_group", "description": "foobar"})

        handle_form_submission.side_effect = call_on_success

        controller.post()

        assert group_create_service.create_private_group.call_args_list == [
            mock.call(name="my_new_group", userid="ariadna", description="foobar")
        ]

    def test_post_redirects_if_form_valid(
        self,
        controller,
        handle_form_submission,
        matchers,
        group_create_service,
        factories,
    ):
        group = factories.Group()
        group_create_service.create_private_group.return_value = group

        # If the form submission is valid then handle_form_submission() should
        # return the redirect that on_success() returns.
        def return_on_success(  # pylint: disable=unused-argument
            request, form, on_success, on_failure
        ):
            return on_success({"name": "my_new_group"})

        handle_form_submission.side_effect = return_on_success

        response = controller.post()

        assert response == matchers.Redirect303To(f"/g/{group.pubid}/{group.slug}")

    def test_post_does_not_create_group_if_form_invalid(
        self, controller, group_create_service, handle_form_submission
    ):
        # If the form submission is invalid then handle_form_submission() should
        # call on_failure().
        def call_on_failure(  # pylint: disable=unused-argument
            request, form, on_success, on_failure
        ):
            on_failure()

        handle_form_submission.side_effect = call_on_failure

        controller.post()

        assert not group_create_service.create_private_group.called

    def test_post_returns_template_data_if_form_invalid(
        self, controller, handle_form_submission
    ):
        # If the form submission is invalid then handle_form_submission() should
        # return the template data that on_failure() returns.
        def return_on_failure(  # pylint: disable=unused-argument
            request, form, on_success, on_failure
        ):
            return on_failure()

        handle_form_submission.side_effect = return_on_failure

        assert controller.post() == {"form": controller.form.render.return_value}

    @pytest.fixture
    def controller(self, pyramid_request):
        return views.GroupCreateController(pyramid_request)

    @pytest.fixture
    def handle_form_submission(self, patch):
        return patch("h.views.groups.form.handle_form_submission")


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


def form_validating_to(appstruct):
    form = mock.Mock()
    form.validate.return_value = appstruct
    form.render.return_value = "valid form"
    return form


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("group_read", "/g/{pubid}/{slug}")
