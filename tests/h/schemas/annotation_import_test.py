# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from contextlib import contextmanager
import pytest

from h.schemas import ValidationError
from h.schemas.annotation_import import AnnotationImportSchema


class TestAnnotationImportSchema(object):

    def test_empty_dictionary(self, schema):
        with pytest.raises(ValidationError):
            schema.validate({})

    def test_comment_annotation(self, schema, comment):
        assert schema.validate(comment) == comment

    def test_reply_annotation(self, schema, reply):
        assert schema.validate(reply) == reply

    @pytest.mark.parametrize('key', ('@context', 'id', 'type', 'created',
                                     'modified', 'creator', 'body',
                                     'motivation', 'target'))
    def test_missing_key(self, schema, comment, key):
        del comment[key]
        with pytest.raises(ValidationError):
            schema.validate(comment)

    def test_wrong_context(self, schema, comment):
        bad_context = 'http://json-ld.org/contexts/person.jsonld'
        comment['@context'] = bad_context
        with raises_error_starting('@context: '):
            schema.validate(comment)

    def test_wrong_type(self, schema, comment):
        comment['type'] = 'Badger'
        with raises_error_starting('type: '):
            schema.validate(comment)

    def test_invalid_motivation(self, schema, comment):
        comment['motivation'] = 'indeterminate'
        with raises_error_starting('motivation: '):
            schema.validate(comment)

    @pytest.mark.parametrize('created', ('2017', 'yesterday', '2017-02-12'))
    def test_invalid_created(self, schema, comment, created):
        comment['created'] = created
        with raises_error_starting('created: '):
            schema.validate(comment)

    @pytest.mark.parametrize('modified', ('2017', 'yesterday', '2017-02-12'))
    def test_invalid_modified(self, schema, comment, modified):
        comment['modified'] = modified
        with raises_error_starting('modified: '):
            schema.validate(comment)

    @pytest.mark.parametrize('creator', ('', 'bob', 'bob@example.com', 6,
                                         'http://example.com'))
    def test_invalid_creator(self, schema, comment, creator):
        comment['creator'] = creator
        with raises_error_starting('creator: '):
            schema.validate(comment)

    def test_no_body(self, schema, comment):
        comment['body'] = []
        with raises_error_starting('body: '):
            schema.validate(comment)

    def test_multiple_bodies(self, schema, comment):
        comment['body'] = [comment['body'][0], comment['body'][0]]
        with raises_error_starting('body: '):
            schema.validate(comment)

    @pytest.mark.parametrize('body_key', ('format', 'type', 'value'))
    def test_no_body_type(self, schema, comment, body_key):
        del comment['body'][0][body_key]
        with raises_error_starting('body.0: '):
            schema.validate(comment)

    @pytest.mark.parametrize('target', ('', 'bob', 'bob@example.com'))
    def test_invalid_target(self, schema, comment, target):
        comment['target'] = target
        with raises_error_starting('target: '):
            schema.validate(comment)

    def test_unknown_property(self, schema, comment):
        comment['synergy'] = 'enterprise'
        with pytest.raises(ValidationError):
            schema.validate(comment)

    @pytest.fixture
    def schema(self):
        return AnnotationImportSchema()

    @pytest.fixture
    def comment(self):
        return {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": "import:123456789",
            "type": "Annotation",
            "created": "2017-01-25T23:00:00Z",
            "modified": "2017-01-25T23:30:00Z",
            "creator": "acct:commenter@example.com",
            "body": [
                {
                    "type": "TextualBody",
                    "value": "Hi",
                    "format": "text/markdown"
                }
            ],
            "motivation": "commenting",
            "target": "https://example.com/foo"
        }

    @pytest.fixture
    def reply(self):
        return {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": "import:987654321",
            "type": "Annotation",
            "created": "2017-01-25T23:00:00Z",
            "modified": "2017-01-25T23:30:00Z",
            "creator": "acct:commenter@example.com",
            "body": [
                {
                    "type": "TextualBody",
                    "value": "Hi yourself",
                    "format": "text/markdown"
                }
            ],
            "motivation": "commenting",
            "target": "import:123456789"
        }


@contextmanager
def raises_error_starting(prefix):
    """Test whether a code block raises a particular ValidationError."""
    with pytest.raises(ValidationError) as error:
        yield

    assert error.value.message.startswith(prefix)
