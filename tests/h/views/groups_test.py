# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import deform
import mock
import pytest
from pyramid.httpexceptions import HTTPMovedPermanently

from h.views import groups as views
from h.models import Group, User
from h.models.group import JoinableBy
from h.services.group_create import GroupCreateService


@pytest.mark.usefixtures("group_create_service", "handle_form_submission", "routes")
class TestGroupCreateController(object):
    def test_get_renders_form(self, controller):
        controller.form = form_validating_to({})

        result = controller.get()

        assert result == {"form": "valid form"}

    def test_post_calls_handle_form_submission(
        self, controller, handle_form_submission, matchers
    ):
        controller.post()

        handle_form_submission.assert_called_once_with(
            controller.request,
            controller.form,
            matchers.AnyCallable(),
            matchers.AnyCallable(),
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
        def call_on_success(request, form, on_success, on_failure):
            on_success({"name": "my_new_group", "description": "foobar"})

        handle_form_submission.side_effect = call_on_success

        controller.post()

        assert group_create_service.create_private_group.call_args_list == [
            mock.call(name="my_new_group", userid="ariadna", description="foobar")
        ]

    def test_post_redirects_if_form_valid(
        self, controller, handle_form_submission, matchers
    ):
        # If the form submission is valid then handle_form_submission() should
        # return the redirect that on_success() returns.
        def return_on_success(request, form, on_success, on_failure):
            return on_success({"name": "my_new_group"})

        handle_form_submission.side_effect = return_on_success

        assert controller.post() == matchers.Redirect303To("/g/abc123/fake-group")

    def test_post_does_not_create_group_if_form_invalid(
        self, controller, group_create_service, handle_form_submission
    ):
        # If the form submission is invalid then handle_form_submission() should
        # call on_failure().
        def call_on_failure(request, form, on_success, on_failure):
            on_failure()

        handle_form_submission.side_effect = call_on_failure

        controller.post()

        assert not group_create_service.create_private_group.called

    def test_post_returns_template_data_if_form_invalid(
        self, controller, handle_form_submission
    ):
        # If the form submission is invalid then handle_form_submission() should
        # return the template data that on_failure() returns.
        def return_on_failure(request, form, on_success, on_failure):
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
class TestGroupEditController(object):
    def test_get_reads_group_properties(self, pyramid_request):
        pyramid_request.create_form.return_value = FakeForm()

        creator = User(username="luke", authority="example.org")
        group = Group(
            name="Birdwatcher Community",
            authority="foobar.com",
            description="We watch birds all day long",
            creator=creator,
        )
        group.pubid = "the-test-pubid"

        result = views.GroupEditController(group, pyramid_request).get()

        assert result == {
            "form": {
                "name": "Birdwatcher Community",
                "description": "We watch birds all day long",
            },
            "group_path": "/g/the-test-pubid/birdwatcher-community",
        }

    def test_post_sets_group_properties(self, form_validating_to, pyramid_request):
        creator = User(username="luke", authority="example.org")
        group = Group(
            name="Birdwatcher Community",
            authority="foobar.com",
            description="We watch birds all day long",
            creator=creator,
        )
        group.pubid = "the-test-pubid"

        controller = views.GroupEditController(group, pyramid_request)
        controller.form = form_validating_to(
            {
                "name": "Alligatorwatcher Comm.",
                "description": "We are all about the alligators now",
            }
        )
        controller.post()

        assert group.name == "Alligatorwatcher Comm."
        assert group.description == "We are all about the alligators now"


@pytest.mark.usefixtures("routes")
def test_read_noslug_redirects(pyramid_request):
    group = FakeGroup("abc123", "some-slug")

    with pytest.raises(HTTPMovedPermanently) as exc:
        views.read_noslug(group, pyramid_request)

    assert exc.value.location == "/g/abc123/some-slug"


class FakeGroup(object):
    def __init__(self, pubid, slug, joinable_by=JoinableBy.authority):
        self.pubid = pubid
        self.slug = slug
        self.joinable_by = joinable_by


class FakeForm(object):
    def set_appstruct(self, appstruct):
        self.appstruct = appstruct

    def render(self):
        return self.appstruct


def form_validating_to(appstruct):
    form = mock.Mock()
    form.validate.return_value = appstruct
    form.render.return_value = "valid form"
    return form


def invalid_form():
    form = mock.Mock()
    form.validate.side_effect = deform.ValidationFailure(None, None, None)
    form.render.return_value = "invalid form"
    return form


@pytest.fixture
def group_create_service(pyramid_config):
    service = mock.create_autospec(GroupCreateService, spec_set=True, instance=True)
    service.create_private_group.return_value = FakeGroup("abc123", "fake-group")
    pyramid_config.register_service(service, name="group_create")
    return service


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route("group_read", "/g/{pubid}/{slug}")
