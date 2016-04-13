# -*- coding: utf-8 -*-

import pytest


@pytest.mark.functional
class TestAPI(object):
    def test_annotation_read(self, app, annotation):
        """Fetch an annotation by ID."""
        res = app.get('/api/annotations/' + annotation.id,
                      headers={'accept': 'application/json'})
        data = res.json
        assert data['id'] == annotation.id

    def test_annotation_read_jsonld(self, app, annotation):
        """Fetch an annotation by ID in jsonld format."""
        res = app.get('/api/annotations/' + annotation.id + '.jsonld')
        data = res.json
        assert data['@context'] == 'http://www.w3.org/ns/anno.jsonld'
        assert data['id'] == 'http://localhost/a/' + annotation.id


@pytest.fixture
def annotation(config):
    from h.api.models.elastic import Annotation
    ann = Annotation({
        'created': '2016-01-01T00:00:00.000000+00:00',
        'updated': '2016-01-01T00:00:00.000000+00:00',
        'user': 'acct:testuser@localhost',
        'target': [{'source': 'http://foobar.com', 'selector': []}],
        'text': 'My test annotation',
        'permissions': {'read': ['group:__world__'],
                        'update': ['acct:testuser@localhost'],
                        'delete': ['acct:testuser@localhost'],
                        'admin': ['acct:testuser@localhost']},
    })
    ann.save()
    return ann
