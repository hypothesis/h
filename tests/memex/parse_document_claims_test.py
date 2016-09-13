import mock
import pytest

from memex import parse_document_claims


class TestDocumentURIsFromLinks(object):

    def test_it_ignores_href_links_that_match_the_claimant_uri(self):
        """
        Links containing only the claimant URI should be ignored.

        If document.link contains a link dict with just an "href" and no other
        keys, and the value of the "href" key is the same as the claimant URI,
        then this link dict should be ignored and not produce an additional
        document URI dict in the output (since the document URI that it would
        generate would be the same as the "self-claim" claimant URI one that is
        always generated anyway).

        """
        claimant = 'http://localhost:5000/docs/help'
        link_dicts = [{'href': claimant}]

        document_uris = parse_document_claims.document_uris_from_links(
            link_dicts,
            claimant,
        )

        assert document_uris == []

    def test_it_ignores_doi_links(self):
        """
        Links containing only an href that starts with doi should be ignored.

        If document.link contains a link dict with just an "href" and no other
        keys, and the value of the "href" key begins with "doi:", then the link
        dict should be ignored and not produce a document URI dict in the
        output.

        This is because document URI dicts for doi: URIs are generate
        separately from other metadata in the document dict outside of the
        "link" list.

        """
        link_dicts = [{'href': 'doi:10.3389/fenvs.2014.00003'}]

        document_uris = parse_document_claims.document_uris_from_links(
            link_dicts,
            claimant='http://localhost:5000/docs/help'
        )

        assert document_uris == []

    def test_it_ignores_highwire_pdf_links(self):
        pdf_url = 'http://example.com/example.pdf'
        link_dicts = [{'href': pdf_url, 'type': 'application/pdf'}]

        document_uris = parse_document_claims.document_uris_from_links(
            link_dicts,
            claimant='http://localhost:5000/docs/help',
        )

        assert document_uris == []

    def test_it_returns_rel_alternate_document_uris_for_rel_alternate_links(
            self):
        alternate_url = 'http://example.com/alternate'
        link_dicts = [{'href': alternate_url, 'rel': 'alternate'}]

        document_uris = parse_document_claims.document_uris_from_links(
            link_dicts,
            claimant='http://localhost:5000/docs/help',
        )

        alternate_document_uri = one(
            [d for d in document_uris if d['type'] == 'rel-alternate'])
        assert alternate_document_uri == {
            'type': 'rel-alternate',
            'claimant': 'http://localhost:5000/docs/help',
            'content_type': '',
            'uri': alternate_url,
        }

    def test_it_uses_link_types_as_document_uri_content_types(self):
        """
        Link types get converted to document URI content_types.

        The value of the 'type' key in link dicts ends up as the value of the
        'content_type' key in the returned document URI dicts.

        """
        link_dicts = [{'href': 'http://example.com/example.html',
                       'type': 'text/html'}]

        document_uris = parse_document_claims.document_uris_from_links(
            link_dicts,
            claimant='http://example.com/example.html',
        )

        assert one(
            [d for d in document_uris if d.get('content_type') == 'text/html'])

    def test_it_returns_multiple_document_URI_dicts(self):
        """If there are multiple claims it should return multiple dicts."""
        link_dicts = [
            {
                'href': 'http://example.com/example.html',
                'type': 'text/html'
            },
            {
                'href': 'http://example.com/alternate.html',
                'rel': 'alternate'
            },
            {
                'href': 'http://example.com/example2.html',
                'type': 'text/html'
            },
        ]

        document_uris = parse_document_claims.document_uris_from_links(
            link_dicts,
            claimant='http://example.com/claimant.html',
        )

        assert len(document_uris) == 3


class TestDocumentMetasFromData(object):

    @pytest.mark.parametrize("input_,output", [
        # String values get turned into length 1 lists.
        (
            {
                'foo': 'string',
            },
            {
                'type': 'foo',
                'value': ['string']
            }
        ),

        # List values get copied over unchanged.
        (
            {
                'foo': ['one', 'two'],
            },
            {
                'type': 'foo',
                'value': ['one', 'two']
            }
        ),

        # Sub-dicts get flattened using a '.' separator in the key,
        # and length 1 list values in sub-dicts get copied over unchanged.
        (
            {
                'facebook': {
                    'description': ['document description'],
                }
            },
            {
                'type': 'facebook.description',
                'value': ['document description']
            }
        ),

        # Length >1 list values in sub-dicts get copied over unchanged.
        (
            {
                'facebook': {
                    'image': [
                        'http://example.com/image1.png',
                        'http://example.com/image2.png',
                        'http://example.com/image3.jpeg',
                    ],
                }
            },
            {
                'type': 'facebook.image',
                'value': [
                    'http://example.com/image1.png',
                    'http://example.com/image2.png',
                    'http://example.com/image3.jpeg'
                ]
            }
        ),

        # String values in sub-dicts get turned into length 1 lists.
        (
            {
                'foo': {
                    'bar': 'string'
                }
            },
            {
                'type': 'foo.bar',
                'value': ['string']
            }
        ),

        # Leading and trailing whitespace gets stripped from document titles.
        (
            {
                'title': ['   My Document',
                          'My Document   ',
                          ' My Document ',
                          '\nMy Document\n\n'],
            },
            {
                'type': 'title',
                'value': ['My Document', 'My Document', 'My Document',
                          'My Document']
            }
        ),
    ])
    def test_document_metas_from_data(self, input_, output):
        claimant = 'http://example.com/claimant/'

        document_metas = parse_document_claims.document_metas_from_data(
            document_data=input_,
            claimant=claimant)

        assert document_metas == [{
            'type': output['type'],
            'value': output['value'],
            'claimant': claimant,
        }]

    def test_document_metas_from_data_ignores_links_list(self):
        """It should ignore the "link" list in the document_data."""
        document_data = {
            'link': [
                {'href': 'http://example.com/link'},
            ]
        }

        document_metas = parse_document_claims.document_metas_from_data(
            document_data, 'http://example/claimant')

        assert document_metas == []

    def test_document_metas_from_data_with_multiple_metadata_claims(self):
        """
        It should create one DocumentMeta for each metadata claim.

        If document_data contains multiple metadata claims it should init one
        DocumentMeta for each claim.

        """
        claimant = 'http://example/claimant'
        document_data = {
            'title': 'the title',
            'description': 'the description',
            'site_title': 'the site title'
        }

        document_metas = parse_document_claims.document_metas_from_data(
            document_data, claimant)

        assert len(document_metas) == len(document_data.items())
        for key, value in document_data.items():
            assert {
                'type': key,
                'value': [value],
                'claimant': claimant,
                } in document_metas

    def test_document_metas_from_data_ignores_null_titles(self):
        """It should ignore null document titles."""
        for title in (None, [None, None]):
            document_data = {'title': title}

            document_metas = parse_document_claims.document_metas_from_data(
                document_data, 'http://example/claimant')

            assert document_metas == []

    def test_document_metas_from_data_ignores_empty_string_titles(self):
        """It should ignore empty document titles."""
        for title in ('', ['', '']):
            document_data = {'title': title}

            document_metas = parse_document_claims.document_metas_from_data(
                document_data, 'http://example/claimant')

            assert document_metas == []

    def test_document_metas_from_data_ignores_whitespace_only_titles(self):
        """It should ignore whitespace-only document titles."""
        for title in (' ', [' ', ' '], '\n\n  \n'):
            document_data = {'title': title}

            document_metas = parse_document_claims.document_metas_from_data(
                document_data, 'http://example/claimant')

            assert document_metas == []


class TestDocumentURIsFromHighwirePDF(object):

    def test_highwire_pdf_values_produce_highwire_pdf_document_uris(self):
        highwire_dict = {
                'pdf_url': ['http://example.com/1.pdf',
                            'http://example.com/2.pdf',
                            'http://example.com/3.pdf'],
        }

        document_uris = parse_document_claims.document_uris_from_highwire_pdf(
            highwire_dict,
            claimant='http://example.com/example.html',
        )

        for pdf in highwire_dict['pdf_url']:
            document_uri = one([d for d in document_uris
                                if d.get('uri') == pdf])
            assert document_uri == {
                'claimant': 'http://example.com/example.html',
                'uri': pdf,
                'type': 'highwire-pdf',
                'content_type': 'application/pdf',
            }


class TestDocumentURIsFromHighwireDOI(object):

    def test_highwire_doi_values_produce_highwire_doi_document_uris(self):
        highwire_dict = {
            'doi': ['doi:10.10.1038/nphys1170', 'doi:10.1002/0470841559.ch1',
                    'doi:10.1594/PANGAEA.726855'],
        }

        document_uris = parse_document_claims.document_uris_from_highwire_doi(
            highwire_dict,
            claimant='http://example.com/example.html',
        )

        for doi in highwire_dict['doi']:
            document_uri = one([d for d in document_uris
                                if d.get('uri') == doi])
            assert document_uri == {
                'claimant': 'http://example.com/example.html',
                'uri': doi,
                'type': 'highwire-doi',
                'content_type': '',
            }

    def test_doi_is_prepended_to_highwire_dois(self):
        """If a highwire DOI doesn't begin with 'doi:' it is prepended."""
        highwire_dict = {'doi': ['10.10.1038/nphys1170']}

        document_uris = parse_document_claims.document_uris_from_highwire_doi(
            highwire_dict,
            claimant='http://example.com/example.html',
        )

        expected_uri = 'doi:' + highwire_dict['doi'][0]
        one([d for d in document_uris if d.get('uri') == expected_uri])


class TestDocumentURIsFromDC(object):

    def test_dc_identifiers_produce_dc_doi_document_uris(self):
        """Each 'identifier' list item in the 'dc' dict becomes a doc URI."""
        dc_dict = {
            'identifier': [
                'doi:10.10.1038/nphys1170',
                'doi:10.1002/0470841559.ch1',
                'doi:10.1594/PANGAEA.726855'
            ]
        }

        document_uris = parse_document_claims.document_uris_from_dc(
            dc_dict,
            claimant='http://example.com/example.html',
        )

        for doi in dc_dict['identifier']:
            document_uri = one([d for d in document_uris
                                if d.get('uri') == doi])
            assert document_uri == {
                'claimant': 'http://example.com/example.html',
                'uri': doi,
                'type': 'dc-doi',
                'content_type': '',
            }

    def test_doi_is_prepended_to_dc_identifiers(self):
        """If a dc identifier doesn't begin with 'doi:' it is prepended."""
        dc_dict = {'identifier': ['10.10.1038/nphys1170']}

        document_uris = parse_document_claims.document_uris_from_dc(
            dc_dict,
            claimant='http://example.com/example.html',
        )

        expected_uri = 'doi:' + dc_dict['identifier'][0]
        one([d for d in document_uris if d.get('uri') == expected_uri])


class TestDocumentURISelfClaim(object):

    def test_document_uri_self_claim(self):
        claimant = 'http://localhost:5000/docs/help'

        document_uri = parse_document_claims.document_uri_self_claim(
            claimant)

        assert document_uri == {
            'claimant': claimant,
            'uri': claimant,
            'type': 'self-claim',
            'content_type': '',
        }


@pytest.mark.usefixtures('document_uris_from_dc',
                         'document_uris_from_highwire_doi',
                         'document_uris_from_highwire_pdf',
                         'document_uris_from_links',
                         'document_uri_self_claim')
class TestDocumentURIsFromData(object):

    def test_it_gets_document_uris_from_links(self, document_uris_from_links):
        document_data = {
            'link': [
                # In production these would be link dicts not strings.
                'link_dict_1',
                'link_dict_2',
                'link_dict_3',
            ]

        }
        claimant = 'http://localhost:5000/docs/help'
        document_uris_from_links.return_value = [
            mock.Mock(), mock.Mock(), mock.Mock()]

        document_uris = parse_document_claims.document_uris_from_data(
            document_data=document_data,
            claimant=claimant,
        )

        document_uris_from_links.assert_called_once_with(
            document_data['link'], claimant)
        for document_uri in document_uris_from_links.return_value:
            assert document_uri in document_uris

    def test_calling_document_uris_from_links_when_no_links(
            self,
            document_uris_from_links):
        document_data = {}  # No 'link' key.
        claimant = 'http://localhost:5000/docs/help'

        parse_document_claims.document_uris_from_data(
            document_data=document_data,
            claimant=claimant,
        )

        document_uris_from_links.assert_called_once_with(
            [], claimant)

    def test_it_gets_documents_uris_from_highwire_pdf(
            self,
            document_uris_from_highwire_pdf):
        document_data = {
            'highwire': {
                'pdf': [
                    'pdf_1',
                    'pdf_2',
                    'pdf_3',
                ]
            }
        }
        claimant = 'http://localhost:5000/docs/help'
        document_uris_from_highwire_pdf.return_value = [
            mock.Mock(), mock.Mock(), mock.Mock()]

        document_uris = parse_document_claims.document_uris_from_data(
            document_data=document_data,
            claimant=claimant,
        )

        document_uris_from_highwire_pdf.assert_called_once_with(
            document_data['highwire'], claimant)
        for document_uri in document_uris_from_highwire_pdf.return_value:
            assert document_uri in document_uris

    def test_calling_document_uris_from_highwire_pdf_when_no_highwire(
            self,
            document_uris_from_highwire_pdf):
        document_data = {}  # No 'highwire' key.
        claimant = 'http://localhost:5000/docs/help'

        parse_document_claims.document_uris_from_data(
            document_data=document_data,
            claimant=claimant,
        )

        document_uris_from_highwire_pdf.assert_called_once_with(
            {}, claimant)

    def test_it_gets_documents_uris_from_highwire_doi(
            self,
            document_uris_from_highwire_doi):
        document_data = {
            'highwire': {
                'doi': [
                    'doi_1',
                    'doi_2',
                    'doi_3',
                ]
            }
        }
        claimant = 'http://localhost:5000/docs/help'
        document_uris_from_highwire_doi.return_value = [
            mock.Mock(), mock.Mock(), mock.Mock()]

        document_uris = parse_document_claims.document_uris_from_data(
            document_data=document_data,
            claimant=claimant,
        )

        document_uris_from_highwire_doi.assert_called_once_with(
            document_data['highwire'], claimant)
        for document_uri in document_uris_from_highwire_doi.return_value:
            assert document_uri in document_uris

    def test_calling_document_uris_from_highwire_doi_when_no_highwire(
            self,
            document_uris_from_highwire_doi):
        document_data = {}  # No 'highwire' key.
        claimant = 'http://localhost:5000/docs/help'

        parse_document_claims.document_uris_from_data(
            document_data=document_data,
            claimant=claimant,
        )

        document_uris_from_highwire_doi.assert_called_once_with(
            {}, claimant)

    def test_it_gets_documents_uris_from_dc(self,
                                            document_uris_from_dc):
        document_data = {
            'dc': {
                'identifier': [
                    'doi_1',
                    'doi_2',
                    'doi_3',
                ]
            }
        }
        claimant = 'http://localhost:5000/docs/help'
        document_uris_from_dc.return_value = [
            mock.Mock(), mock.Mock(), mock.Mock()]

        document_uris = parse_document_claims.document_uris_from_data(
            document_data=document_data,
            claimant=claimant,
        )

        document_uris_from_dc.assert_called_once_with(
            document_data['dc'], claimant)
        for document_uri in document_uris_from_dc.return_value:
            assert document_uri in document_uris

    def test_calling_document_uris_from_dc_when_no_dc(self,
                                                      document_uris_from_dc):
        document_data = {}  # No 'dc' key.
        claimant = 'http://localhost:5000/docs/help'

        parse_document_claims.document_uris_from_data(
            document_data=document_data,
            claimant=claimant,
        )

        document_uris_from_dc.assert_called_once_with(
            {}, claimant)

    def test_it_gets_self_claim_document_uris(self, document_uri_self_claim):
        claimant = 'http://example.com/claimant'

        document_uris = parse_document_claims.document_uris_from_data(
            {}, claimant)

        document_uri_self_claim.assert_called_once_with(claimant)
        assert document_uri_self_claim.return_value in document_uris

    @pytest.fixture
    def document_uris_from_dc(self, patch):
        return patch('memex.parse_document_claims.document_uris_from_dc', return_value=[])

    @pytest.fixture
    def document_uris_from_highwire_pdf(self, patch):
        return patch('memex.parse_document_claims.document_uris_from_highwire_pdf', return_value=[])

    @pytest.fixture
    def document_uris_from_highwire_doi(self, patch):
        return patch('memex.parse_document_claims.document_uris_from_highwire_doi', return_value=[])

    @pytest.fixture
    def document_uris_from_links(self, patch):
        return patch('memex.parse_document_claims.document_uris_from_links', return_value=[])

    @pytest.fixture
    def document_uri_self_claim(self, patch):
        return patch('memex.parse_document_claims.document_uri_self_claim')


def one(list_):
    assert len(list_) == 1
    return list_[0]
