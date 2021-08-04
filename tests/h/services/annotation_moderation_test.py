import pytest

from h.services.annotation_moderation import (
    AnnotationModerationService,
    annotation_moderation_service_factory,
)


class TestAnnotationModerationServiceAllHidden:
    def test_it_lists_moderated_annotation_ids(self, svc, mods):
        ids = [m.annotation.id for m in mods[0:-1]]
        assert svc.all_hidden(ids) == set(ids)

    def test_it_skips_non_moderated_annotations(self, svc, factories):
        annotation = factories.Annotation()

        assert svc.all_hidden([annotation.id]) == set()

    def test_it_handles_with_no_ids(self, svc):
        assert svc.all_hidden([]) == set()

    @pytest.fixture(autouse=True)
    def mods(self, factories):
        return factories.AnnotationModeration.create_batch(3)


class TestAnnotationModerationServiceFactory:
    def test_it_returns_service(self, pyramid_request):
        svc = annotation_moderation_service_factory(None, pyramid_request)
        assert isinstance(svc, AnnotationModerationService)


@pytest.fixture
def svc(db_session):
    return AnnotationModerationService(db_session)
