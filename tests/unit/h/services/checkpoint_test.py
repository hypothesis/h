from datetime import datetime, timedelta
from unittest import mock

import pytest

from h.services.checkpoint import CheckpointService, factory


class TestActiveCheckpoint:
    def test_it_returns_an_unrevealed_checkpoint(self, svc, group, document):
        checkpoint = self.checkpoint(group, document, reveal_date=None)

        assert svc.active_checkpoint(group.id, "http://example.com/page") == checkpoint

    def test_it_returns_a_checkpoint_with_a_future_reveal_date(
        self, svc, group, document
    ):
        checkpoint = self.checkpoint(
            group,
            document,
            reveal_date=datetime.utcnow() + timedelta(days=1),  # noqa: DTZ003
        )

        assert svc.active_checkpoint(group.id, "http://example.com/page") == checkpoint

    def test_it_returns_None_when_the_checkpoint_is_revealed(
        self, svc, group, document
    ):
        self.checkpoint(
            group,
            document,
            reveal_date=datetime.utcnow() - timedelta(days=1),  # noqa: DTZ003
        )

        assert svc.active_checkpoint(group.id, "http://example.com/page") is None

    @pytest.mark.usefixtures("document")
    def test_it_returns_None_when_there_is_no_checkpoint(self, svc, group):
        assert svc.active_checkpoint(group.id, "http://example.com/page") is None

    def test_it_returns_None_for_a_different_group(
        self, svc, group, document, factories
    ):
        self.checkpoint(group, document, reveal_date=None)
        other_group = factories.Group()

        assert svc.active_checkpoint(other_group.id, "http://example.com/page") is None

    def test_it_resolves_the_uri_to_the_document(self, svc, group, document, factories):
        # A second URI on the same document (e.g. a PDF fingerprint) must
        # resolve to the same checkpoint.
        factories.DocumentURI(document=document, uri="urn:x-pdf:the-fingerprint")
        checkpoint = self.checkpoint(group, document, reveal_date=None)

        assert (
            svc.active_checkpoint(group.id, "urn:x-pdf:the-fingerprint") == checkpoint
        )

    def test_it_returns_None_for_an_unknown_uri(self, svc, group, document):
        self.checkpoint(group, document, reveal_date=None)

        assert svc.active_checkpoint(group.id, "http://example.com/other") is None

    def checkpoint(self, group, document, reveal_date):
        return self.factories.Checkpoint(
            group=group, document=document, reveal_date=reveal_date
        )

    @pytest.fixture(autouse=True)
    def _factories(self, factories):
        self.factories = factories

    @pytest.fixture
    def group(self, factories):
        return factories.Group()

    @pytest.fixture
    def document(self, factories):
        document = factories.Document()
        factories.DocumentURI(document=document, uri="http://example.com/page")
        return document


class TestFactory:
    def test_it(self, pyramid_request):
        svc = factory(mock.sentinel.context, pyramid_request)

        assert isinstance(svc, CheckpointService)
        assert svc.db == pyramid_request.db


@pytest.fixture
def svc(db_session):
    return CheckpointService(db=db_session)
