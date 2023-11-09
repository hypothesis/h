import re

import pytest
from h_matchers import Any

from h.util import document_claims
from h.util.document_claims import doi_uri_from_string


class TestDocumentURIsFromLinks:
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
        claimant = "http://localhost:5000/docs/help"
        link_dicts = [{"href": claimant}]

        document_uris = document_claims.document_uris_from_links(link_dicts, claimant)

        assert not document_uris

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
        link_dicts = [{"href": "doi:10.3389/fenvs.2014.00003"}]

        document_uris = document_claims.document_uris_from_links(
            link_dicts, claimant="http://localhost:5000/docs/help"
        )

        assert not document_uris

    def test_it_ignores_highwire_pdf_links(self):
        pdf_url = "http://example.com/example.pdf"
        link_dicts = [{"href": pdf_url, "type": "application/pdf"}]

        document_uris = document_claims.document_uris_from_links(
            link_dicts, claimant="http://localhost:5000/docs/help"
        )

        assert not document_uris

    def test_it_returns_rel_alternate_document_uris_for_rel_alternate_links(self):
        alternate_url = "http://example.com/alternate"
        link_dicts = [{"href": alternate_url, "rel": "alternate"}]

        document_uris = document_claims.document_uris_from_links(
            link_dicts, claimant="http://localhost:5000/docs/help"
        )

        alternate_document_uri = one(
            [d for d in document_uris if d["type"] == "rel-alternate"]
        )
        assert alternate_document_uri == {
            "type": "rel-alternate",
            "claimant": "http://localhost:5000/docs/help",
            "content_type": "",
            "uri": alternate_url,
        }

    def test_it_uses_link_types_as_document_uri_content_types(self):
        """
        Link types get converted to document URI content_types.

        The value of the 'type' key in link dicts ends up as the value of the
        'content_type' key in the returned document URI dicts.

        """
        link_dicts = [{"href": "http://example.com/example.html", "type": "text/html"}]

        document_uris = document_claims.document_uris_from_links(
            link_dicts, claimant="http://example.com/example.html"
        )

        assert one([d for d in document_uris if d.get("content_type") == "text/html"])

    def test_it_returns_multiple_document_URI_dicts(self):
        """If there are multiple claims it should return multiple dicts."""
        link_dicts = [
            {"href": "http://example.com/example.html", "type": "text/html"},
            {"href": "http://example.com/alternate.html", "rel": "alternate"},
            {"href": "http://example.com/example2.html", "type": "text/html"},
        ]

        document_uris = document_claims.document_uris_from_links(
            link_dicts, claimant="http://example.com/claimant.html"
        )

        assert len(document_uris) == 3


class TestDocumentMetasFromData:
    @pytest.mark.parametrize(
        "input_,output",
        [
            # String values get turned into length 1 lists.
            ({"foo": "string"}, {"type": "foo", "value": ["string"]}),
            # List values get copied over unchanged.
            ({"foo": ["one", "two"]}, {"type": "foo", "value": ["one", "two"]}),
            # Sub-dicts get flattened using a '.' separator in the key,
            # and length 1 list values in sub-dicts get copied over unchanged.
            (
                {"facebook": {"description": ["document description"]}},
                {"type": "facebook.description", "value": ["document description"]},
            ),
            # Length >1 list values in sub-dicts get copied over unchanged.
            (
                {
                    "facebook": {
                        "image": [
                            "http://example.com/image1.png",
                            "http://example.com/image2.png",
                            "http://example.com/image3.jpeg",
                        ]
                    }
                },
                {
                    "type": "facebook.image",
                    "value": [
                        "http://example.com/image1.png",
                        "http://example.com/image2.png",
                        "http://example.com/image3.jpeg",
                    ],
                },
            ),
            # String values in sub-dicts get turned into length 1 lists.
            ({"foo": {"bar": "string"}}, {"type": "foo.bar", "value": ["string"]}),
            # Leading and trailing whitespace gets stripped from document titles.
            (
                {
                    "title": [
                        "   My Document",
                        "My Document   ",
                        " My Document ",
                        "\nMy Document\n\n",
                        "\rMy Document\r\n",
                        "\tMy Document \t \t ",
                    ]
                },
                {
                    "type": "title",
                    "value": [
                        "My Document",
                        "My Document",
                        "My Document",
                        "My Document",
                        "My Document",
                        "My Document",
                    ],
                },
            ),
            # Leading and trailing whitespace does not get-stripped from non-titles.
            (
                {
                    "foo": [
                        "   My Document",
                        "My Document   ",
                        " My Document ",
                        "\nMy Document\n\n",
                        "\rMy Document\r\n",
                        "\tMy Document \t \t ",
                    ]
                },
                {
                    "type": "foo",
                    "value": [
                        "   My Document",
                        "My Document   ",
                        " My Document ",
                        "\nMy Document\n\n",
                        "\rMy Document\r\n",
                        "\tMy Document \t \t ",
                    ],
                },
            ),
        ],
    )
    def test_document_metas_from_data(self, input_, output):
        claimant = "http://example.com/claimant/"

        document_metas = document_claims.document_metas_from_data(
            document_data=input_, claimant=claimant
        )

        assert document_metas == [
            {"type": output["type"], "value": output["value"], "claimant": claimant}
        ]

    def test_document_metas_from_data_ignores_links_list(self):
        """It should ignore the "link" list in the document_data."""
        document_data = {"link": [{"href": "http://example.com/link"}]}

        document_metas = document_claims.document_metas_from_data(
            document_data, "http://example/claimant"
        )

        assert not document_metas

    def test_document_metas_from_data_with_multiple_metadata_claims(self):
        """
        It should create one DocumentMeta for each metadata claim.

        If document_data contains multiple metadata claims it should init one
        DocumentMeta for each claim.

        """
        claimant = "http://example/claimant"
        document_data = {
            "title": "the title",
            "description": "the description",
            "site_title": "the site title",
        }

        document_metas = document_claims.document_metas_from_data(
            document_data, claimant
        )

        assert len(document_metas) == len(document_data.items())
        for key, value in document_data.items():
            assert {
                "type": key,
                "value": [value],
                "claimant": claimant,
            } in document_metas

    def test_document_metas_from_data_ignores_null_titles(self):
        """It should ignore null document titles."""
        for title in (None, [None, None]):
            document_data = {"title": title}

            document_metas = document_claims.document_metas_from_data(
                document_data, "http://example/claimant"
            )

            assert not document_metas

    def test_document_metas_from_data_allows_null_non_titles(self):
        """Null values are allowed if 'type' isn't 'title'."""
        for value in (None, [None, None]):
            document_data = {"foo": value}

            document_metas = document_claims.document_metas_from_data(
                document_data, "http://example/claimant"
            )

            if not isinstance(value, list):
                # We expect it to turn non-lists into length-1 lists.
                value = [value]

            assert document_metas == [
                {"type": "foo", "value": value, "claimant": "http://example/claimant"}
            ]

    def test_document_metas_from_data_ignores_empty_string_titles(self):
        """It should ignore empty document titles."""
        for title in ("", ["", ""]):
            document_data = {"title": title}

            document_metas = document_claims.document_metas_from_data(
                document_data, "http://example/claimant"
            )

            assert not document_metas

    def test_document_metas_from_data_allows_empty_string_non_titles(self):
        """Empty strings are allowed if 'type' isn't 'title'."""
        for value in ("", ["", ""]):
            document_data = {"foo": value}

            document_metas = document_claims.document_metas_from_data(
                document_data, "http://example/claimant"
            )

            if not isinstance(value, list):
                # We expect it to turn non-lists into length-1 lists.
                value = [value]

            assert document_metas == [
                {"type": "foo", "value": value, "claimant": "http://example/claimant"}
            ]

    def test_document_metas_from_data_ignores_whitespace_only_titles(self):
        """It should ignore whitespace-only document titles."""
        for title in (" ", [" ", " "], "\n\n  \n"):
            document_data = {"title": title}

            document_metas = document_claims.document_metas_from_data(
                document_data, "http://example/claimant"
            )

            assert not document_metas

    def test_document_metas_from_data_allows_whitespace_only_non_titles(self):
        """Whitespace-only strings are allowed if 'type' isn't 'title'."""
        for value in (" ", [" ", " "], "\n\n  \n"):
            document_data = {"foo": value}

            document_metas = document_claims.document_metas_from_data(
                document_data, "http://example/claimant"
            )

            if not isinstance(value, list):
                # We expect it to turn non-lists into length-1 lists.
                value = [value]

            assert document_metas == [
                {"type": "foo", "value": value, "claimant": "http://example/claimant"}
            ]


class TestDocumentURIsFromHighwirePDF:
    def test_highwire_pdf_values_produce_highwire_pdf_document_uris(self):
        highwire_dict = {
            "pdf_url": [
                "http://example.com/1.pdf",
                "http://example.com/2.pdf",
                "http://example.com/3.pdf",
            ]
        }

        document_uris = document_claims.document_uris_from_highwire_pdf(
            highwire_dict, claimant="http://example.com/example.html"
        )

        for pdf in highwire_dict["pdf_url"]:
            document_uri = one([d for d in document_uris if d.get("uri") == pdf])
            assert document_uri == {
                "claimant": "http://example.com/example.html",
                "uri": pdf,
                "type": "highwire-pdf",
                "content_type": "application/pdf",
            }


class TestDOIURIFromString:
    @pytest.mark.parametrize("doi", ["10.1001/1234", "doi:10.1001/1234"])
    def test_it_prepends_doi_prefix(self, doi):
        assert doi_uri_from_string(doi) == f"doi:{strip_prefix('doi:', doi)}"

    @pytest.mark.parametrize(
        "url",
        [
            "http://doi.org/10.1234/5678",
            "https://doi.org/10.1234/5678",
            "http://dx.doi.org/10.1234/5678",
            "https://dx.doi.org/10.1234/5678",
        ],
    )
    def test_it_allows_doi_urls(self, url):
        # Many sites store DOI URLs rather than just identifiers in DOI fields.
        # We should ideally normalize the different forms, but for now we just
        # continue to accept them.
        assert doi_uri_from_string(url) == f"doi:{url}"

    @pytest.mark.parametrize(
        "doi",
        [
            # Empty
            "doi:",
            "",
            # Whitespace only
            "doi: ",
            " ",
            # Strings that do not match the DOI syntax.
            "9.1234/567",
            "chapter1/section1",
            "1234.5678",
            "10.0.0.1",
            "10.0/1234",
            # Non-DOI URLs
            "https://publisher.org/foo.html",
        ],
    )
    def test_it_returns_none_if_invalid(self, doi):
        assert doi_uri_from_string(doi) is None

    @pytest.mark.parametrize("doi", ["  doi: 10.1234/5678"])
    def test_it_strips_whitespace(self, doi):
        assert doi_uri_from_string(doi) == re.sub("\\s+", "", doi)


class TestDocumentURIsFromHighwireDOI:
    def test_highwire_doi_values_produce_highwire_doi_document_uris(self):
        highwire_dict = {
            "doi": [
                "doi:10.1038/nphys1170",
                "doi:10.1002/0470841559.ch1",
                "doi:10.1594/PANGAEA.726855",
            ]
        }

        document_uris = document_claims.document_uris_from_highwire_doi(
            highwire_dict, claimant="http://example.com/example.html"
        )

        for doi in highwire_dict["doi"]:
            document_uri = one([d for d in document_uris if d.get("uri") == doi])
            assert document_uri == {
                "claimant": "http://example.com/example.html",
                "uri": doi,
                "type": "highwire-doi",
                "content_type": "",
            }

    def test_it_ignores_invalid_dois(self):
        """If `doi_uri_from_string` returns `None`, the identifier is ignored."""
        highwire_dict = {"doi": ["doi:"]}
        document_uris = document_claims.document_uris_from_highwire_doi(
            highwire_dict, claimant="http://example.com/example.html"
        )
        assert not document_uris


class TestDocumentURIsFromDC:
    def test_dc_identifiers_produce_dc_doi_document_uris(self):
        """Each 'identifier' list item in the 'dc' dict becomes a doc URI."""
        dc_dict = {
            "identifier": [
                "doi:10.1038/nphys1170",
                "doi:10.1002/0470841559.ch1",
                "doi:10.1594/PANGAEA.726855",
            ]
        }

        document_uris = document_claims.document_uris_from_dc(
            dc_dict, claimant="http://example.com/example.html"
        )

        for doi in dc_dict["identifier"]:
            document_uri = one([d for d in document_uris if d.get("uri") == doi])
            assert document_uri == {
                "claimant": "http://example.com/example.html",
                "uri": doi,
                "type": "dc-doi",
                "content_type": "",
            }

    def test_it_ignores_invalid_dois(self):
        """If `doi_uri_from_string` returns `None`, the identifier is ignored."""
        dc_dict = {"identifier": ["doi:"]}
        document_uris = document_claims.document_uris_from_dc(
            dc_dict, claimant="http://example.com/example.html"
        )
        assert not document_uris


class TestDocumentURISelfClaim:
    def test_document_uri_self_claim(self):
        claimant = "http://localhost:5000/docs/help"

        document_uri = document_claims.document_uri_self_claim(claimant)

        assert document_uri == {
            "claimant": claimant,
            "uri": claimant,
            "type": "self-claim",
            "content_type": "",
        }


@pytest.mark.usefixtures(
    "document_uris_from_dc",
    "document_uris_from_highwire_doi",
    "document_uris_from_highwire_pdf",
    "document_uris_from_links",
    "document_uri_self_claim",
)
class TestDocumentURIsFromData:
    def test_it_gets_document_uris_from_links(self, document_uris_from_links):
        document_data = {
            "link": [
                # In production these would be link dicts not strings.
                "link_dict_1",
                "link_dict_2",
                "link_dict_3",
            ]
        }
        claimant = "http://localhost:5000/docs/help"
        document_uris_from_links.return_value = [
            {"uri": "uri_1"},
            {"uri": "uri_2"},
            {"uri": "uri_3"},
        ]

        document_uris = document_claims.document_uris_from_data(
            document_data=document_data, claimant=claimant
        )

        document_uris_from_links.assert_called_once_with(
            document_data["link"], claimant
        )
        for document_uri in document_uris_from_links.return_value:
            assert document_uri in document_uris

    def test_calling_document_uris_from_links_when_no_links(
        self, document_uris_from_links
    ):
        document_data = {}  # No 'link' key.
        claimant = "http://localhost:5000/docs/help"

        document_claims.document_uris_from_data(
            document_data=document_data, claimant=claimant
        )

        document_uris_from_links.assert_called_once_with([], claimant)

    def test_it_gets_documents_uris_from_highwire_pdf(
        self, document_uris_from_highwire_pdf
    ):
        document_data = {"highwire": {"pdf": ["pdf_1", "pdf_2", "pdf_3"]}}
        claimant = "http://localhost:5000/docs/help"
        document_uris_from_highwire_pdf.return_value = [
            {"uri": "uri_1"},
            {"uri": "uri_2"},
            {"uri": "uri_3"},
        ]

        document_uris = document_claims.document_uris_from_data(
            document_data=document_data, claimant=claimant
        )

        document_uris_from_highwire_pdf.assert_called_once_with(
            document_data["highwire"], claimant
        )
        for document_uri in document_uris_from_highwire_pdf.return_value:
            assert document_uri in document_uris

    def test_calling_document_uris_from_highwire_pdf_when_no_highwire(
        self, document_uris_from_highwire_pdf
    ):
        document_data = {}  # No 'highwire' key.
        claimant = "http://localhost:5000/docs/help"

        document_claims.document_uris_from_data(
            document_data=document_data, claimant=claimant
        )

        document_uris_from_highwire_pdf.assert_called_once_with({}, claimant)

    def test_it_gets_documents_uris_from_highwire_doi(
        self, document_uris_from_highwire_doi
    ):
        document_data = {"highwire": {"doi": ["doi_1", "doi_2", "doi_3"]}}
        claimant = "http://localhost:5000/docs/help"
        document_uris_from_highwire_doi.return_value = [
            {"uri": "uri_1"},
            {"uri": "uri_2"},
            {"uri": "uri_3"},
        ]

        document_uris = document_claims.document_uris_from_data(
            document_data=document_data, claimant=claimant
        )

        document_uris_from_highwire_doi.assert_called_once_with(
            document_data["highwire"], claimant
        )
        for document_uri in document_uris_from_highwire_doi.return_value:
            assert document_uri in document_uris

    def test_calling_document_uris_from_highwire_doi_when_no_highwire(
        self, document_uris_from_highwire_doi
    ):
        document_data = {}  # No 'highwire' key.
        claimant = "http://localhost:5000/docs/help"

        document_claims.document_uris_from_data(
            document_data=document_data, claimant=claimant
        )

        document_uris_from_highwire_doi.assert_called_once_with({}, claimant)

    def test_it_gets_documents_uris_from_dc(self, document_uris_from_dc):
        document_data = {"dc": {"identifier": ["doi_1", "doi_2", "doi_3"]}}
        claimant = "http://localhost:5000/docs/help"
        document_uris_from_dc.return_value = [
            {"uri": "uri_1"},
            {"uri": "uri_2"},
            {"uri": "uri_3"},
        ]

        document_uris = document_claims.document_uris_from_data(
            document_data=document_data, claimant=claimant
        )

        document_uris_from_dc.assert_called_once_with(document_data["dc"], claimant)
        for document_uri in document_uris_from_dc.return_value:
            assert document_uri in document_uris

    def test_calling_document_uris_from_dc_when_no_dc(self, document_uris_from_dc):
        document_data = {}  # No 'dc' key.
        claimant = "http://localhost:5000/docs/help"

        document_claims.document_uris_from_data(
            document_data=document_data, claimant=claimant
        )

        document_uris_from_dc.assert_called_once_with({}, claimant)

    def test_it_gets_self_claim_document_uris(self, document_uri_self_claim):
        claimant = "http://example.com/claimant"

        document_uris = document_claims.document_uris_from_data({}, claimant)

        document_uri_self_claim.assert_called_once_with(claimant)
        assert document_uri_self_claim.return_value in document_uris

    def test_it_ignores_null_uris(
        self,
        document_uris_from_links,
        document_uris_from_highwire_pdf,
        document_uris_from_highwire_doi,
        document_uris_from_dc,
        document_uri_self_claim,
    ):
        document_uris_from_links.return_value = [{"uri": None}]
        document_uris_from_highwire_pdf.return_value = [{"uri": None}]
        document_uris_from_highwire_doi.return_value = [{"uri": None}]
        document_uris_from_dc.return_value = [{"uri": None}]
        document_uri_self_claim.return_value = {"uri": None}

        document_uris = document_claims.document_uris_from_data(
            {}, "http://example.com/claimant"
        )

        assert document_uris == []

    def test_it_ignores_empty_string_uris(
        self,
        document_uris_from_links,
        document_uris_from_highwire_pdf,
        document_uris_from_highwire_doi,
        document_uris_from_dc,
        document_uri_self_claim,
    ):
        document_uris_from_links.return_value = [{"uri": ""}]
        document_uris_from_highwire_pdf.return_value = [{"uri": ""}]
        document_uris_from_highwire_doi.return_value = [{"uri": ""}]
        document_uris_from_dc.return_value = [{"uri": ""}]
        document_uri_self_claim.return_value = {"uri": ""}

        document_uris = document_claims.document_uris_from_data(
            {}, "http://example.com/claimant"
        )

        assert document_uris == []

    def test_it_ignores_whitespace_only_self_claim_uris(self, document_uri_self_claim):
        for uri in (" ", "\n ", "\r\n", " \t"):
            document_uri_self_claim.return_value = {"uri": uri}

            document_uris = document_claims.document_uris_from_data(
                {}, "http://example.com/claimant"
            )

            assert document_uris == []

    def test_it_ignores_whitespace_only_uris(
        self,
        document_uris_from_links,
        document_uris_from_highwire_pdf,
        document_uris_from_highwire_doi,
        document_uris_from_dc,
        document_uri_self_claim,
    ):
        uris = [" ", "\n ", "\r\n", " \t"]
        document_uris_from_links.return_value = [{"uri": u} for u in uris]
        document_uris_from_highwire_pdf.return_value = [{"uri": u} for u in uris]
        document_uris_from_highwire_doi.return_value = [{"uri": u} for u in uris]
        document_uris_from_dc.return_value = [{"uri": u} for u in uris]

        document_uris = document_claims.document_uris_from_data(
            {}, "http://example.com/claimant"
        )

        assert document_uris == [document_uri_self_claim.return_value]

    def test_it_strips_whitespace_from_uris(
        self,
        document_uris_from_links,
        document_uris_from_highwire_pdf,
        document_uris_from_highwire_doi,
        document_uris_from_dc,
        document_uri_self_claim,
    ):
        document_uris_from_links.return_value = [
            {"uri": " from_link_1"},
            {"uri": "from_link_2 "},
            {"uri": " from_link_3 "},
        ]
        document_uris_from_highwire_pdf.return_value = [
            {"uri": " highwire_1"},
            {"uri": "highwire_2 "},
            {"uri": " highwire_3 "},
        ]
        document_uris_from_highwire_doi.return_value = [
            {"uri": " doi_1"},
            {"uri": "doi_2 "},
            {"uri": " doi_3 "},
        ]
        document_uris_from_dc.return_value = [
            {"uri": " dc_1"},
            {"uri": "dc_2 "},
            {"uri": " dc_3 "},
        ]

        document_uris = document_claims.document_uris_from_data(
            {}, "http://example.com/claimant"
        )

        assert (
            document_uris
            == Any.list.containing(
                [
                    {"uri": "from_link_1"},
                    {"uri": "from_link_2"},
                    {"uri": "from_link_3"},
                    {"uri": "highwire_1"},
                    {"uri": "highwire_2"},
                    {"uri": "highwire_3"},
                    {"uri": "doi_1"},
                    {"uri": "doi_2"},
                    {"uri": "doi_3"},
                    {"uri": "dc_1"},
                    {"uri": "dc_2"},
                    {"uri": "dc_3"},
                    document_uri_self_claim.return_value,
                ]
            ).only()
        )

    def test_it_strips_whitespace_from_self_claim_uris(
        self, document_uris_from_links, document_uri_self_claim
    ):
        for uri in (" self_claim", "self_claim ", " self_claim "):
            document_uris_from_links.return_value = []
            document_uri_self_claim.return_value = {"uri": uri}

            document_uris = document_claims.document_uris_from_data(
                {}, "http://example.com/claimant"
            )

            assert document_uris == [{"uri": uri.strip()}]

    @pytest.fixture
    def document_uris_from_dc(self, patch):
        return patch("h.util.document_claims.document_uris_from_dc", return_value=[])

    @pytest.fixture
    def document_uris_from_highwire_pdf(self, patch):
        return patch(
            "h.util.document_claims.document_uris_from_highwire_pdf", return_value=[]
        )

    @pytest.fixture
    def document_uris_from_highwire_doi(self, patch):
        return patch(
            "h.util.document_claims.document_uris_from_highwire_doi", return_value=[]
        )

    @pytest.fixture
    def document_uris_from_links(self, patch):
        return patch("h.util.document_claims.document_uris_from_links", return_value=[])

    @pytest.fixture
    def document_uri_self_claim(self, patch):
        return patch("h.util.document_claims.document_uri_self_claim")


def one(list_):
    assert len(list_) == 1
    return list_[0]


def strip_prefix(prefix, s):
    if s.startswith(prefix):
        return s[len(prefix) :]
    return s
