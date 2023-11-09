from h import models
from h.presenters.document_json import DocumentJSONPresenter


class TestDocumentJSONPresenter:
    def test_asdict(self, db_session):
        document = models.Document(
            title="Foo",
            document_uris=[
                models.DocumentURI(uri="http://foo.com", claimant="http://foo.com"),
                models.DocumentURI(
                    uri="http://foo.org",
                    claimant="http://foo.com",
                    type="rel-canonical",
                ),
            ],
        )
        db_session.add(document)
        db_session.flush()

        presenter = DocumentJSONPresenter(document)
        expected = {"title": ["Foo"]}
        assert expected == presenter.asdict()

    def test_asdict_when_none_document(self):
        assert not DocumentJSONPresenter(None).asdict()

    def test_asdict_does_not_render_other_meta_than_title(self, db_session):
        document = models.Document(
            title="Foo",
            meta=[
                models.DocumentMeta(
                    type="title", value=["Foo"], claimant="http://foo.com"
                ),
                models.DocumentMeta(
                    type="twitter.url",
                    value=["http://foo.com"],
                    claimant="http://foo.com",
                ),
                models.DocumentMeta(
                    type="facebook.title", value=["FB Title"], claimant="http://foo.com"
                ),
            ],
        )
        db_session.add(document)
        db_session.flush()

        presenter = DocumentJSONPresenter(document)
        assert {"title": ["Foo"]} == presenter.asdict()
