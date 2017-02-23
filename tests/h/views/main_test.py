# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
from pyramid import httpexceptions
import pytest

from memex.models.annotation import Annotation
from memex.models.document import Document
from memex.resources import AnnotationResource
from h.views import main


def _fake_sidebar_app(request, extra):
    return extra


@pytest.mark.usefixtures('routes')
def test_og_document(annotation_document, document_title, pyramid_request,
                     group_service, links_service, sidebar_app):
    annotation = Annotation(id='123', userid='foo', target_uri='http://example.com')
    context = AnnotationResource(annotation, group_service, links_service)
    document = Document()
    annotation_document.return_value = document
    document_title.return_value = 'WikiHow — How to Make a ☆Starmap☆'
    sidebar_app.side_effect = _fake_sidebar_app

    ctx = main.annotation_page(context, pyramid_request)

    def test(d):
        return 'foo' in d['content'] and 'Starmap' in d['content']
    assert any(test(d) for d in ctx['meta_attrs'])


@pytest.mark.usefixtures('routes')
def test_og_no_document(pyramid_request, group_service, links_service, sidebar_app):
    annotation = Annotation(id='123', userid='foo', target_uri='http://example.com')
    context = AnnotationResource(annotation, group_service, links_service)
    sidebar_app.side_effect = _fake_sidebar_app

    ctx = main.annotation_page(context, pyramid_request)

    def test(d):
        return 'foo' in d['content']
    assert any(test(d) for d in ctx['meta_attrs'])


@pytest.mark.usefixtures('sidebar_app', 'routes')
class TestStreamUserRedirect(object):

    def test_it_redirects_to_activity_page_with_tags(self, pyramid_request):
        pyramid_request.params['q'] = 'tag:foo'
        pyramid_request.matchdict['tag'] = 'foo'
        with pytest.raises(httpexceptions.HTTPFound) as exc:
            main.stream(None, pyramid_request)

        assert exc.value.location == 'http://example.com/search?q=tag%3Afoo'

    def test_it_redirects_to_activity_page_with_tags_containing_spaces(self, pyramid_request):
        pyramid_request.params['q'] = 'tag:foo bar'
        pyramid_request.matchdict['tag'] = 'foo bar'
        with pytest.raises(httpexceptions.HTTPFound) as exc:
            main.stream(None, pyramid_request)

        assert exc.value.location == 'http://example.com/search?q=tag%3A%22foo+bar%22'

    def test_it_redirects_to_activity_page_if_q_length_great_than_2(self, sidebar_app, pyramid_request):
        pyramid_request.params['q'] = 'tag:foo:bar'
        pyramid_request.matchdict['tag'] = 'foo:bar'
        with pytest.raises(httpexceptions.HTTPFound) as exc:
            main.stream(None, pyramid_request)

        assert exc.value.location == 'http://example.com/search?q=tag%3Afoo%3Abar'

    def test_it_does_not_redirect_to_activity_page_if_no_q_param(self, sidebar_app, pyramid_request):
        pyramid_request.matchdict['tag'] = 'foo'

        main.stream(None, pyramid_request)

        assert sidebar_app.called

    def test_it_does_not_redirect_to_activity_page_if_no_tag_key(self, sidebar_app, pyramid_request):
        pyramid_request.params['q'] = 'foo'

        main.stream(None, pyramid_request)

        assert sidebar_app.called

    def test_it_does_not_redirect_to_activity_page_if_no_tag_key_value(self, sidebar_app, pyramid_request):
        pyramid_request.params['q'] = 'tag-foo'

        main.stream(None, pyramid_request)

        assert sidebar_app.called

    def test_it_redirects_to_user_activity_page(self, pyramid_request):
        pyramid_request.matchdict['user'] = 'bob'

        with pytest.raises(httpexceptions.HTTPFound) as exc:
            main.stream_user_redirect(pyramid_request)

        assert exc.value.location == 'http://example.com/user/bob'

    def test_it_extracts_username_from_account_id(self, pyramid_request):
        pyramid_request.matchdict['user'] = 'acct:bob@hypothes.is'

        with pytest.raises(httpexceptions.HTTPFound) as exc:
            main.stream_user_redirect(pyramid_request)

        assert exc.value.location == 'http://example.com/user/bob'

    @pytest.fixture
    def routes(self, pyramid_config):
        pyramid_config.add_route('activity.search', '/search')
        pyramid_config.add_route('activity.user_search', '/user/{username}')
        pyramid_config.add_route('stream', '/stream')
        pyramid_config.add_route('stream_atom', '/stream.atom')
        pyramid_config.add_route('stream_rss', '/stream.rss')


@pytest.fixture
def sidebar_app(patch):
    return patch('h.views.main.sidebar_app')


@pytest.fixture
def annotation_document(patch):
    return patch('memex.models.annotation.Annotation.document',
                 autospec=None,
                 new_callable=mock.PropertyMock)


@pytest.fixture
def document_title(patch):
    return patch('memex.models.document.Document.title',
                 autospec=None,
                 new_callable=mock.PropertyMock)


@pytest.fixture
def pyramid_config(pyramid_config):
    # Pretend the client assets environment has been configured
    pyramid_config.registry['assets_client_env'] = mock.Mock()
    return pyramid_config


@pytest.fixture
def routes(pyramid_config):
    pyramid_config.add_route('api.annotation', '/api/ann/{id}')
    pyramid_config.add_route('api.index', '/api/index')
    pyramid_config.add_route('assets_client', '/assets/client')
    pyramid_config.add_route('index', '/index')


@pytest.fixture
def group_service(pyramid_config):
    group_service = mock.Mock(spec_set=['find'])
    pyramid_config.register_service(group_service, iface='memex.interfaces.IGroupService')
    return group_service


@pytest.fixture
def links_service(pyramid_config):
    service = mock.Mock(spec_set=['get', 'get_all'])
    pyramid_config.register_service(service, name='links')
    return service
