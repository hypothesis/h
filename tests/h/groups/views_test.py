# -*- coding: utf-8 -*-

import deform
import mock
import pytest
from pyramid.httpexceptions import (HTTPMovedPermanently, HTTPNoContent,
                                    HTTPSeeOther)

from h.groups import views


@pytest.mark.usefixtures('groups_service', 'routes')
class TestGroupCreateController(object):

    def test_get_renders_form(self, pyramid_request):
        controller = views.GroupCreateController(pyramid_request)
        controller.form = form_validating_to({})

        result = controller.get()

        assert result == {'form': 'valid form'}

    def test_post_creates_group_when_form_valid(self,
                                                groups_service,
                                                pyramid_config,
                                                pyramid_request):
        pyramid_config.testing_securitypolicy('ariadna')
        controller = views.GroupCreateController(pyramid_request)
        controller.form = form_validating_to({'name': 'Kangaroo Tamers'})

        controller.post()

        assert ('Kangaroo Tamers', 'ariadna') in groups_service.created

    def test_post_redirects_to_group_when_form_valid(self,
                                                     pyramid_config,
                                                     pyramid_request):
        pyramid_config.testing_securitypolicy('ariadna')
        controller = views.GroupCreateController(pyramid_request)
        controller.form = form_validating_to({'name': 'Kangaroo Tamers'})

        result = controller.post()

        assert isinstance(result, HTTPSeeOther)
        assert result.location == '/g/abc123/fake-group'


    def test_post_rerenders_form_when_form_invalid(self,
                                                   pyramid_config,
                                                   pyramid_request):
        pyramid_config.testing_securitypolicy('ariadna')
        controller = views.GroupCreateController(pyramid_request)
        controller.form = invalid_form()

        result = controller.post()

        assert result == {'form': 'invalid form'}


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

        assert result == {
            'group': group,
            'document_links': ['link1', 'link2'],
        }

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
