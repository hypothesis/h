# -*- coding: utf-8 -*-

import deform
import mock
import pytest
from pyramid.httpexceptions import (HTTPMovedPermanently, HTTPNoContent,
                                    HTTPSeeOther)

from h.groups import views


@pytest.mark.usefixtures('groups_service', 'handle_form_submission', 'routes')
class TestGroupCreateController(object):

    def test_get_renders_form(self, controller):
        controller.form = form_validating_to({})

        result = controller.get()

        assert result == {'form': 'valid form'}

    def test_post_calls_handle_form_submission(self,
                                               controller,
                                               handle_form_submission,
                                               matchers):
        controller.post()

        handle_form_submission.assert_called_once_with(
            controller.request,
            controller.form,
            matchers.any_callable(),
            matchers.any_callable(),
        )

    def test_post_returns_handle_form_submission(self,
                                                 controller,
                                                 handle_form_submission):
        assert controller.post() == handle_form_submission.return_value

    def test_post_creates_new_group_if_form_valid(self,
                                                  controller,
                                                  groups_service,
                                                  handle_form_submission,
                                                  pyramid_config):
        pyramid_config.testing_securitypolicy('ariadna')

        # If the form submission is valid then handle_form_submission() should
        # call on_success() with the appstruct.
        def call_on_success(request, form, on_success, on_failure):
            on_success({'name': 'my_new_group'})
        handle_form_submission.side_effect = call_on_success

        controller.post()

        assert groups_service.created == [('my_new_group', 'ariadna')]

    def test_post_redirects_if_form_valid(self,
                                          controller,
                                          handle_form_submission,
                                          matchers):
        # If the form submission is valid then handle_form_submission() should
        # return the redirect that on_success() returns.
        def return_on_success(request, form, on_success, on_failure):
            return on_success({'name': 'my_new_group'})
        handle_form_submission.side_effect = return_on_success

        assert controller.post() == matchers.redirect_303_to(
            '/g/abc123/fake-group')

    def test_post_does_not_create_group_if_form_invalid(self,
                                                        controller,
                                                        groups_service,
                                                        handle_form_submission):
        # If the form submission is invalid then handle_form_submission() should
        # call on_failure().
        def call_on_failure(request, form, on_success, on_failure):
            on_failure()
        handle_form_submission.side_effect = call_on_failure

        controller.post()

        assert groups_service.created == []

    def test_post_returns_template_data_if_form_invalid(self,
                                                        controller,
                                                        handle_form_submission):
        # If the form submission is invalid then handle_form_submission() should
        # return the template data that on_failure() returns.
        def return_on_failure(request, form, on_success, on_failure):
            return on_failure()
        handle_form_submission.side_effect = return_on_failure

        assert controller.post() == {'form': controller.form.render.return_value}

    @pytest.fixture
    def controller(self, pyramid_request):
        return views.GroupCreateController(pyramid_request)

    @pytest.fixture
    def handle_form_submission(self, patch):
        return patch('h.groups.views.form.handle_form_submission')


@pytest.mark.usefixtures('groups_service', 'routes')
class TestGroupRead(object):
    def test_redirects_if_slug_incorrect(self, pyramid_request):
        group = FakeGroup('abc123', 'some-slug')
        pyramid_request.matchdict['slug'] = 'another-slug'

        with pytest.raises(HTTPMovedPermanently) as exc:
            views.read(group, pyramid_request)

        assert exc.value.location == '/g/abc123/some-slug'

    def test_returns_template_context(self, patch, pyramid_request):
        group = FakeGroup('abc123', 'some-slug')
        group.documents = lambda: ['d1', 'd2']
        link = patch('h.presenters.DocumentHTMLPresenter.link',
                     autospec=None,
                     new_callable=mock.PropertyMock)
        link.side_effect = ['link1', 'link2']
        pyramid_request.matchdict['slug'] = 'some-slug'

        result = views.read(group, pyramid_request)

        assert result['group'] == group
        assert result['document_links'] == ['link1', 'link2']

    def test_renders_join_template_if_not_member(self,
                                                 pyramid_config,
                                                 pyramid_request):
        group = FakeGroup('abc123', 'some-slug')
        pyramid_config.testing_securitypolicy('bohus', permissive=False)
        pyramid_request.matchdict['slug'] = 'some-slug'

        result = views.read(group, pyramid_request)

        assert 'join.html' in pyramid_request.override_renderer
        assert result == {'group': group}


@pytest.mark.usefixtures('routes')
class TestGroupReadUnauthenticated(object):
    def test_redirects_if_slug_incorrect(self, pyramid_request):
        group = FakeGroup('abc123', 'some-slug')
        pyramid_request.matchdict['slug'] = 'another-slug'

        with pytest.raises(HTTPMovedPermanently) as exc:
            views.read_unauthenticated(group, pyramid_request)

        assert exc.value.location == '/g/abc123/some-slug'

    def test_returns_template_context(self, pyramid_request):
        group = FakeGroup('abc123', 'some-slug')
        pyramid_request.matchdict['slug'] = 'some-slug'

        result = views.read_unauthenticated(group, pyramid_request)

        assert result == {'group': group}


@pytest.mark.usefixtures('routes')
def test_read_noslug_redirects(pyramid_request):
    group = FakeGroup('abc123', 'some-slug')

    with pytest.raises(HTTPMovedPermanently) as exc:
        views.read_noslug(group, pyramid_request)

    assert exc.value.location == '/g/abc123/some-slug'


@pytest.mark.usefixtures('groups_service', 'routes')
class TestGroupJoin(object):
    def test_joins_group(self,
                         groups_service,
                         pyramid_config,
                         pyramid_request):
        group = FakeGroup('abc123', 'some-slug')
        pyramid_config.testing_securitypolicy('gentiana')

        views.join(group, pyramid_request)

        assert (group, 'gentiana') in groups_service.joined

    def test_redirects_to_group_page(self, pyramid_request):
        group = FakeGroup('abc123', 'some-slug')

        result = views.join(group, pyramid_request)

        assert isinstance(result, HTTPSeeOther)
        assert result.location == '/g/abc123/some-slug'


@pytest.mark.usefixtures('groups_service', 'routes')
class TestGroupLeave(object):
    def test_leaves_group(self,
                          groups_service,
                          pyramid_config,
                          pyramid_request):
        group = FakeGroup('abc123', 'some-slug')
        pyramid_config.testing_securitypolicy('marcela')

        views.leave(group, pyramid_request)

        assert (group, 'marcela') in groups_service.left

    def test_returns_nocontent(self, pyramid_request):
        group = FakeGroup('abc123', 'some-slug')

        result = views.leave(group, pyramid_request)

        assert isinstance(result, HTTPNoContent)


class FakeGroup(object):
    def __init__(self, pubid, slug):
        self.pubid = pubid
        self.slug = slug

class FakeGroupsService(object):
    def __init__(self):
        self.created = []
        self.joined = []
        self.left = []

    def create(self, name, userid):
        self.created.append((name, userid))
        return FakeGroup('abc123', 'fake-group')

    def member_join(self, group, userid):
        self.joined.append((group, userid))

    def member_leave(self, group, userid):
        self.left.append((group, userid))



def form_validating_to(appstruct):
    form = mock.Mock()
    form.validate.return_value = appstruct
    form.render.return_value = 'valid form'
    return form


def invalid_form():
    form = mock.Mock()
    form.validate.side_effect = deform.ValidationFailure(None, None, None)
    form.render.return_value = 'invalid form'
    return form


@pytest.fixture
def groups_service(pyramid_config):
    service = FakeGroupsService()
    pyramid_config.register_service(service, name='groups')
    return service


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('group_read', '/g/{pubid}/{slug}')
