# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from h import models
from h.services.annotation_moderation import AnnotationModerationService
from h.services.annotation_moderation import annotation_moderation_service_factory


class TestAnnotationModerationServiceHide(object):
    def test_it_creates_annotation_moderation(self, svc, factories, db_session):
        annotation = factories.Annotation()
        svc.hide(annotation)

        mod = db_session.query(models.AnnotationModeration) \
                        .filter_by(annotation=annotation) \
                        .first()

        assert mod is not None

    def test_it_skips_creating_moderation_when_already_exists(self, svc, factories, db_session):
        existing = factories.AnnotationModeration()

        svc.hide(existing.annotation)

        count = db_session.query(models.AnnotationModeration) \
                          .filter_by(annotation=existing.annotation) \
                          .count()

        assert count == 1

    @pytest.fixture
    def svc(self, db_session):
        return AnnotationModerationService(db_session)


class TestAnnotationNipsaServiceFactory(object):
    def test_it_returns_service(self, pyramid_request):
        svc = annotation_moderation_service_factory(None, pyramid_request)
        assert isinstance(svc, AnnotationModerationService)

    def test_it_provides_request_db_as_session(self, pyramid_request):
        svc = annotation_moderation_service_factory(None, pyramid_request)
        assert svc.session == pyramid_request.db
