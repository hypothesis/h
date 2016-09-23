# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest


@pytest.mark.functional
class TestAPI(object):
    def test_annotation_read(self, app, annotation):
        """Fetch an annotation by ID."""
        res = app.get('/api/annotations/' + annotation.id,
                      headers={b'accept': b'application/json'})
        data = res.json
        assert data['id'] == annotation.id

    def test_annotation_read_jsonld(self, app, annotation):
        """Fetch an annotation by ID in jsonld format."""
        res = app.get('/api/annotations/' + annotation.id + '.jsonld')
        data = res.json
        assert data['@context'] == 'http://www.w3.org/ns/anno.jsonld'
        assert data['id'] == 'http://localhost/a/' + annotation.id


@pytest.fixture
def annotation(db_session, factories):
    ann =  factories.Annotation(userid='acct:testuser@localhost',
                                groupid='__world__',
                                shared=True)
    db_session.commit()
    return ann
