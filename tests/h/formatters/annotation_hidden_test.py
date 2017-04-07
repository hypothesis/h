# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import namedtuple

import pytest

from h.formatters.annotation_hidden import AnnotationHiddenFormatter
from h.services.annotation_moderation import AnnotationModerationService

FakeAnnotationResource = namedtuple('FakeAnnotationResource', ['annotation'])


class TestAnnotationHiddenFormatter(object):
    def test_preload_sets_founds_hidden_annotations_to_true(self, annotations, formatter):
        annotation_ids = [a.id for a in annotations['hidden']]

        expected = {id_: True for id_ in annotation_ids}
        assert formatter.preload(annotation_ids) == expected

    def test_preload_sets_missing_flags_to_false(self, annotations, formatter):
        annotation_ids = [a.id for a in annotations['public']]

        expected = {id_: False for id_ in annotation_ids}
        assert formatter.preload(annotation_ids) == expected

    def test_format_for_hidden_annotation(self, formatter, factories):
        mod = factories.AnnotationModeration()
        resource = FakeAnnotationResource(mod.annotation)
        assert formatter.format(resource) == {'hidden': True}

    def test_format_for_public_annotation(self, formatter, factories):
        annotation = factories.Annotation()
        resource = FakeAnnotationResource(annotation)

        assert formatter.format(resource) == {'hidden': False}

    def test_format_for_hidden_annotation_as_annotation_author(self, formatter, factories, current_user):
        annotation = factories.Annotation(userid=current_user.userid)
        resource = FakeAnnotationResource(annotation)
        factories.AnnotationModeration(annotation=annotation)

        assert formatter.format(resource) == {'hidden': False}

    def test_format_works_for_missing_user(self, moderation_svc, factories):
        formatter = AnnotationHiddenFormatter(moderation_svc)
        mod = factories.AnnotationModeration()
        resource = FakeAnnotationResource(mod.annotation)
        assert formatter.format(resource) == {'hidden': True}

    @pytest.fixture
    def current_user(self, factories):
        return factories.User()

    @pytest.fixture
    def formatter(self, moderation_svc, current_user):
        return AnnotationHiddenFormatter(moderation_svc, current_user)

    @pytest.fixture
    def moderation_svc(self, db_session):
        return AnnotationModerationService(db_session)

    @pytest.fixture
    def annotations(self, factories):
        hidden = [mod.annotation for mod in factories.AnnotationModeration.create_batch(3)]
        public = factories.Annotation.create_batch(2)
        return {'hidden': hidden, 'public': public}
