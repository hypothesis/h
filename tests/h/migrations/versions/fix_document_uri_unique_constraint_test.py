from __future__ import unicode_literals

from h.models import Document, DocumentURI
from h import fix_document_uri_unique_constraint as migration


def add_test_data(db_session):
    # The DocumentURI's that we'll have in the db before upgrade().
    before_upgrade = []

    # The DocumentURI's that we expect to see in the db after upgrade().
    expected = []

    # DocumentURI's with unique values in all fields and no nulls,
    # these should be untouched by upgrade().
    before_upgrade.extend([
        DocumentURI(claimant='http://example.com/1',
                    uri='http://example.com/1',
                    type='type_1',
                    content_type='content_type_1'),
        DocumentURI(claimant='http://example.com/2',
                    uri='http://example.com/2',
                    type='type_2',
                    content_type='content_type_2')
    ])
    expected.extend([
        DocumentURI(claimant='http://example.com/1',
                    uri='http://example.com/1',
                    type='type_1',
                    content_type='content_type_1'),
        DocumentURI(claimant='http://example.com/2',
                    uri='http://example.com/2',
                    type='type_2',
                    content_type='content_type_2')
    ])

    # DocumentURI's with unique values but with null in the type column.
    # These should just have their type changed to ''.
    before_upgrade.extend([
        DocumentURI(claimant='http://example.com/3',
                    uri='http://example.com/3',
                    type=None,
                    content_type='content_type_3'),
        DocumentURI(claimant='http://example.com/4',
                    uri='http://example.com/4',
                    type=None,
                    content_type='content_type_4')
    ])
    expected.extend([
        DocumentURI(claimant='http://example.com/3',
                    uri='http://example.com/3',
                    type='',
                    content_type='content_type_3'),
        DocumentURI(claimant='http://example.com/4',
                    uri='http://example.com/4',
                    type='',
                    content_type='content_type_4')
    ])

    # DocumentURI's with unique values but with null in the content_type
    # column. These should just have their content_type changed to ''.
    before_upgrade.extend([
        DocumentURI(claimant='http://example.com/5',
                    uri='http://example.com/5',
                    type='type_5',
                    content_type=None),
        DocumentURI(claimant='http://example.com/6',
                    uri='http://example.com/6',
                    type='type_6',
                    content_type=None)
    ])
    expected.extend([
        DocumentURI(claimant='http://example.com/5',
                    uri='http://example.com/5',
                    type='type_5',
                    content_type=''),
        DocumentURI(claimant='http://example.com/6',
                    uri='http://example.com/6',
                    type='type_6',
                    content_type='')
    ])

    # DocumentURIs with the same values for all fields, but with null for type.
    # All but the most recent of these should be deleted, and the most recent
    # one should have its type changed to ''.
    before_upgrade.extend([
        DocumentURI(claimant='http://example.com/7',
                    uri='http://example.com/7',
                    type=None,
                    content_type='content_type_7'),
        DocumentURI(claimant='http://example.com/7',
                    uri='http://example.com/7',
                    type=None,
                    content_type='content_type_7'),
        DocumentURI(claimant='http://example.com/7',
                    uri='http://example.com/7',
                    type=None,
                    content_type='content_type_7'),
    ])
    expected.extend([
        DocumentURI(claimant='http://example.com/7',
                    uri='http://example.com/7',
                    type='',
                    content_type='content_type_7')
    ])

    # DocumentURIs with the same values for all fields, but with null for
    # content_type.  All but the most recent of these should be deleted, and
    # the most recent one should have its content_type changed to ''.
    before_upgrade.extend([
        DocumentURI(claimant='http://example.com/8',
                    uri='http://example.com/8',
                    type='type_8',
                    content_type=None),
        DocumentURI(claimant='http://example.com/8',
                    uri='http://example.com/8',
                    type='type_8',
                    content_type=None),
        DocumentURI(claimant='http://example.com/8',
                    uri='http://example.com/8',
                    type='type_8',
                    content_type=None),
    ])
    expected.extend([
        DocumentURI(claimant='http://example.com/8',
                    uri='http://example.com/8',
                    type='type_8',
                    content_type='')
    ])

    # DocumentURIs with the same values for all fields, but with null for both
    # the type and the content_type. All but the most recent of these should be
    # deleted, and the most recent one should have its type and content_type
    # changed to ''.
    before_upgrade.extend([
        DocumentURI(claimant='http://example.com/9',
                    uri='http://example.com/9',
                    type=None,
                    content_type=None),
        DocumentURI(claimant='http://example.com/9',
                    uri='http://example.com/9',
                    type=None,
                    content_type=None),
        DocumentURI(claimant='http://example.com/9',
                    uri='http://example.com/9',
                    type=None,
                    content_type=None),
    ])
    expected.extend([
        DocumentURI(claimant='http://example.com/9',
                    uri='http://example.com/9',
                    type='',
                    content_type='')
    ])

    # DocumentURIs with the same claimant and uri but one with a null type,
    # one with a null content_type, and one with both null type and
    # content_type. All three of these should remain but with their null values
    # changed to empty strings.
    before_upgrade.extend([
        DocumentURI(claimant='http://example.com/10',
                    uri='http://example.com/10',
                    type=None,
                    content_type='content_type_10'),
        DocumentURI(claimant='http://example.com/10',
                    uri='http://example.com/10',
                    type='type_10',
                    content_type=None),
        DocumentURI(claimant='http://example.com/10',
                    uri='http://example.com/10',
                    type=None,
                    content_type=None),
    ])
    expected.extend([
        DocumentURI(claimant='http://example.com/10',
                    uri='http://example.com/10',
                    type='',
                    content_type='content_type_10'),
        DocumentURI(claimant='http://example.com/10',
                    uri='http://example.com/10',
                    type='type_10',
                    content_type=''),
        DocumentURI(claimant='http://example.com/10',
                    uri='http://example.com/10',
                    type='',
                    content_type=''),
    ])

    document = Document()
    for document_uri in before_upgrade:
        document_uri.document = document

    db_session.add_all(before_upgrade)

    return before_upgrade, expected


def test_upgrade(db_session):
    _, expected = add_test_data(db_session)
    db_session.commit()
    migration.merge_duplicate_document_uris(db_session)
    migration.change_nulls_to_empty_strings(db_session)
    db_session.commit()

    remaining_document_uris = db_session.query(DocumentURI).all()

    assert len(remaining_document_uris) == len(expected)

    def find_document_uri(target, document_uris):
        for doc_uri in document_uris:
            if (doc_uri.claimant_normalized == target.claimant_normalized and
                    doc_uri.uri_normalized == target.uri_normalized and
                    doc_uri.type == target.type and
                    doc_uri.content_type == target.content_type):
                return True
        return False

    for document_uri in expected:
        assert find_document_uri(document_uri, remaining_document_uris)
