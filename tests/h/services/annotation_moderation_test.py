# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h import models
from h.services.annotation_moderation import AnnotationModerationService
from h.services.annotation_moderation import annotation_moderation_service_factory


class TestAnnotationModerationServiceHidden(object):
    def test_it_returns_true_for_moderated_annotation(self, svc, factories):
        mod = factories.AnnotationModeration()

        assert svc.hidden(mod.annotation) is True

    def test_it_returns_false_for_non_moderated_annotation(self, svc, factories):
        annotation = factories.Annotation()

        assert svc.hidden(annotation) is False


@pytest.mark.usefixtures("mods")
class TestAnnotationModerationServiceAllHidden(object):
    def test_it_lists_moderated_annotation_ids(self, svc, mods):
        ids = [m.annotation.id for m in mods[0:-1]]
        assert svc.all_hidden(ids) == set(ids)

    def test_it_skips_non_moderated_annotations(self, svc, factories):
        annotation = factories.Annotation()

        assert svc.all_hidden([annotation.id]) == set()

    def test_it_handles_with_no_ids(self, svc):
        assert svc.all_hidden([]) == set()

    @pytest.fixture
    def mods(self, factories):
        return factories.AnnotationModeration.create_batch(3)


class TestAnnotationModerationServiceHide(object):
    def test_it_creates_annotation_moderation(self, svc, factories, db_session):
        annotation = factories.Annotation()
        svc.hide(annotation)

        mod = (
            db_session.query(models.AnnotationModeration)
            .filter_by(annotation=annotation)
            .first()
        )

        assert mod is not None

    def test_it_skips_creating_moderation_when_already_exists(
        self, svc, factories, db_session
    ):
        existing = factories.AnnotationModeration()

        svc.hide(existing.annotation)

        count = (
            db_session.query(models.AnnotationModeration)
            .filter_by(annotation=existing.annotation)
            .count()
        )

        assert count == 1


class TestAnnotationModerationServiceUnhide(object):
    def test_it_unhides_given_annotation(self, svc, factories, db_session):
        mod = factories.AnnotationModeration()
        annotation = mod.annotation

        svc.unhide(annotation)

        assert svc.hidden(annotation) is False

    def test_it_leaves_othes_annotations_hidden(self, svc, factories, db_session):
        mod1, mod2 = factories.AnnotationModeration(), factories.AnnotationModeration()

        svc.unhide(mod1.annotation)

        assert svc.hidden(mod2.annotation) is True

    def test_it_skips_hiding_annotation_when_not_hidden(
        self, svc, factories, db_session
    ):
        annotation = factories.Annotation()

        svc.unhide(annotation)

        assert svc.hidden(annotation) is False


class TestAnnotationNipsaServiceFactory(object):
    def test_it_returns_service(self, pyramid_request):
        svc = annotation_moderation_service_factory(None, pyramid_request)
        assert isinstance(svc, AnnotationModerationService)

    def test_it_provides_request_db_as_session(self, pyramid_request):
        svc = annotation_moderation_service_factory(None, pyramid_request)
        assert svc.session == pyramid_request.db


@pytest.fixture
def svc(db_session):
    return AnnotationModerationService(db_session)
