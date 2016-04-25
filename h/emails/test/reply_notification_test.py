# -*- coding: utf-8 -*-

import datetime

import mock
from pyramid.testing import DummyRequest
import pytest

from h.api.models import elastic
from h.emails.reply_notification import generate
from h.models import Annotation
from h.models import Document, DocumentMeta
from h.models import User
from h.notification.reply_template import Notification


@pytest.mark.usefixtures('routes', 'token_serializer')
class TestGenerate(object):

    def test_calls_renderers_with_appropriate_context(self,
                                                      req,
                                                      notification,
                                                      parent_user,
                                                      reply_user,
                                                      html_renderer,
                                                      text_renderer):
        generate(req, notification)

        expected_context = {
            'document_title': 'My fascinating page',
            'document_url': 'http://example.org/',
            'parent': notification.parent,
            'parent_url': 'http://example.com/ann/foo123',
            'parent_user': parent_user,
            'reply': notification.reply,
            'reply_url': 'http://example.com/ann/bar456',
            'reply_user': reply_user,
            'reply_user_url': 'http://example.com/stream/user/ron',
            'unsubscribe_url': 'http://example.com/unsub/FAKETOKEN',
        }
        html_renderer.assert_(**expected_context)
        text_renderer.assert_(**expected_context)

    def test_falls_back_to_target_uri_for_document_title(self,
                                                         req,
                                                         notification,
                                                         storage_driver,
                                                         html_renderer,
                                                         text_renderer):
        if storage_driver == 'elastic':
            notification.document['title'] = []
        else:
            notification.document.meta[0].value = []

        generate(req, notification)

        html_renderer.assert_(document_title='http://example.org/')
        text_renderer.assert_(document_title='http://example.org/')

    def test_returns_text_and_body_results_from_renderers(self,
                                                          req,
                                                          notification,
                                                          html_renderer,
                                                          text_renderer):
        html_renderer.string_response = 'HTML output'
        text_renderer.string_response = 'Text output'

        _, _, text, html = generate(req, notification)

        assert html == 'HTML output'
        assert text == 'Text output'

    @pytest.mark.usefixtures('html_renderer', 'text_renderer')
    def test_returns_subject_with_reply_username(self, req, notification):
        _, subject, _, _ = generate(req, notification)

        assert subject == 'ron has replied to your annotation'

    @pytest.mark.usefixtures('html_renderer', 'text_renderer')
    def test_returns_parent_email_as_recipients(self, req, notification):
        recipients, _, _, _ = generate(req, notification)

        assert recipients == ['pat@ric.ia']

    @pytest.mark.usefixtures('html_renderer', 'text_renderer')
    def test_calls_token_serializer_with_correct_arguments(self,
                                                           req,
                                                           notification,
                                                           token_serializer):
        generate(req, notification)

        token_serializer.dumps.assert_called_once_with({
            'type': 'reply',
            'uri': 'acct:patricia@example.com',
        })

    def test_jinja_templates_render(self, config, req, notification):
        """Ensure that the jinja templates don't contain syntax errors"""
        config.include('pyramid_jinja2')
        config.add_jinja2_extension('h.jinja_extensions.Filters')

        generate(req, notification)

    @pytest.fixture
    def routes(self, config):
        config.add_route('annotation', '/ann/{id}')
        config.add_route('stream.user_query', '/stream/user/{user}')
        config.add_route('unsubscribe', '/unsub/{token}')

    @pytest.fixture
    def req(self):
        return DummyRequest(auth_domain='example.com')

    @pytest.fixture
    def html_renderer(self, config):
        return config.testing_add_renderer('h:templates/emails/reply_notification.html.jinja2')

    @pytest.fixture
    def text_renderer(self, config):
        return config.testing_add_renderer('h:templates/emails/reply_notification.txt.jinja2')

    @pytest.fixture
    def document(self, storage_driver):
        title = 'My fascinating page'
        if storage_driver == 'elastic':
            return elastic.Document(title=[title])
        else:
            doc = Document()
            doc.meta.append(DocumentMeta(type='title', value=[title]))
            return doc

    @pytest.fixture
    def parent(self, storage_driver):
        common = {
            'id': 'foo123',
            'created': datetime.datetime.utcnow(),
            'updated': datetime.datetime.utcnow(),
            'text': 'Foo is true',
        }
        uri = 'http://example.org/'
        if storage_driver == 'elastic':
            return elastic.Annotation(uri=uri, **common)
        else:
            return Annotation(target_uri=uri, **common)

    @pytest.fixture
    def reply(self, storage_driver):
        common = {
            'id': 'bar456',
            'created': datetime.datetime.utcnow(),
            'updated': datetime.datetime.utcnow(),
            'text': 'No it is not!',
        }
        uri = 'http://example.org/'
        if storage_driver == 'elastic':
            return elastic.Annotation(uri=uri, **common)
        else:
            return Annotation(target_uri=uri, **common)

    @pytest.fixture
    def notification(self, reply, reply_user, parent, parent_user, document):
        return Notification(reply=reply,
                            reply_user=reply_user,
                            parent=parent,
                            parent_user=parent_user,
                            document=document)

    @pytest.fixture
    def parent_user(self):
        return User(username='patricia', email='pat@ric.ia')

    @pytest.fixture
    def reply_user(self):
        return User(username='ron', email='ron@thesmiths.com')

    @pytest.fixture(params=['elastic', 'postgres'])
    def storage_driver(self, request):
        return request.param

    @pytest.fixture
    def token_serializer(self, config):
        serializer = mock.Mock(spec_set=['dumps'])
        serializer.dumps.return_value = 'FAKETOKEN'
        config.registry.notification_serializer = serializer
        return serializer
