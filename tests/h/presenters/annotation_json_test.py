# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime

import mock
import pytest

from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy

from h.presenters.annotation_json import AnnotationJSONPresenter
from memex.resources import AnnotationResource


class TestAnnotationJSONPresenter(object):
    def test_asdict(self, document_asdict, group_service, fake_links_service):
        ann = mock.Mock(id='the-id',
                        created=datetime.datetime(2016, 2, 24, 18, 3, 25, 768),
                        updated=datetime.datetime(2016, 2, 29, 10, 24, 5, 564),
                        userid='acct:luke',
                        target_uri='http://example.com',
                        text='It is magical!',
                        tags=['magic'],
                        groupid='__world__',
                        shared=True,
                        target_selectors=[{'TestSelector': 'foobar'}],
                        references=['referenced-id-1', 'referenced-id-2'],
                        extra={'extra-1': 'foo', 'extra-2': 'bar'})
        resource = AnnotationResource(ann, group_service, fake_links_service)

        document_asdict.return_value = {'foo': 'bar'}

        expected = {'id': 'the-id',
                    'created': '2016-02-24T18:03:25.000768+00:00',
                    'updated': '2016-02-29T10:24:05.000564+00:00',
                    'user': 'acct:luke',
                    'uri': 'http://example.com',
                    'text': 'It is magical!',
                    'tags': ['magic'],
                    'group': '__world__',
                    'permissions': {'read': ['group:__world__'],
                                    'admin': ['acct:luke'],
                                    'update': ['acct:luke'],
                                    'delete': ['acct:luke']},
                    'target': [{'source': 'http://example.com',
                                'selector': [{'TestSelector': 'foobar'}]}],
                    'document': {'foo': 'bar'},
                    'links': {'giraffe': 'http://giraffe.com',
                              'toad': 'http://toad.net'},
                    'references': ['referenced-id-1', 'referenced-id-2'],
                    'extra-1': 'foo',
                    'extra-2': 'bar'}

        result = AnnotationJSONPresenter(resource).asdict()

        assert result == expected

    def test_asdict_extra_cannot_override_other_data(self, document_asdict, group_service, fake_links_service):
        ann = mock.Mock(id='the-real-id', extra={'id': 'the-extra-id'})
        resource = AnnotationResource(ann, group_service, fake_links_service)
        document_asdict.return_value = {}

        presented = AnnotationJSONPresenter(resource).asdict()
        assert presented['id'] == 'the-real-id'

    def test_asdict_extra_uses_copy_of_extra(self, document_asdict, group_service, fake_links_service):
        extra = {'foo': 'bar'}
        ann = mock.Mock(id='my-id', extra=extra)
        resource = AnnotationResource(ann, group_service, fake_links_service)
        document_asdict.return_value = {}

        AnnotationJSONPresenter(resource).asdict()

        # Presenting the annotation shouldn't change the "extra" dict.
        assert extra == {'foo': 'bar'}

    @pytest.mark.usefixtures('policy')
    @pytest.mark.parametrize('annotation,group_readable,action,expected', [
        (mock.Mock(userid='acct:luke', shared=False), 'world', 'read', ['acct:luke']),
        (mock.Mock(userid='acct:luke', groupid='abcde', shared=False), 'members', 'read', ['acct:luke']),
        (mock.Mock(groupid='__world__', shared=True), 'world', 'read', ['group:__world__']),
        (mock.Mock(groupid='lulapalooza', shared=True), 'members', 'read', ['group:lulapalooza']),
        (mock.Mock(groupid='publisher', shared=True), 'world', 'read', ['group:__world__']),
        (mock.Mock(userid='acct:luke'), None, 'admin', ['acct:luke']),
        (mock.Mock(userid='acct:luke'), None, 'update', ['acct:luke']),
        (mock.Mock(userid='acct:luke'), None, 'delete', ['acct:luke']),
        ])
    def test_permissions(self, annotation, group_readable, action, expected, group_service, fake_links_service):
        annotation.deleted = False

        group_principals = {
            'members': (security.Allow, 'group:{}'.format(annotation.groupid), 'read'),
            'world': (security.Allow, security.Everyone, 'read'),
            None: security.DENY_ALL,
        }
        group = mock.Mock(spec_set=['__acl__'])
        group.__acl__.return_value = [group_principals[group_readable]]
        group_service.find.return_value = group

        resource = AnnotationResource(annotation, group_service, fake_links_service)
        presenter = AnnotationJSONPresenter(resource)
        assert expected == presenter.permissions[action]

    @pytest.fixture
    def document_asdict(self, patch):
        return patch('h.presenters.annotation_json.DocumentJSONPresenter.asdict')

    @pytest.fixture
    def policy(self, pyramid_config):
        """Set up a fake authentication policy with a real ACL authorization policy."""
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(None)
        pyramid_config.set_authorization_policy(policy)
