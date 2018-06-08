# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from collections import namedtuple

import pytest

from h.formatters.annotation_hidden import AnnotationHiddenFormatter
from h.services.annotation_moderation import AnnotationModerationService

FakeAnnotationContext = namedtuple("FakeAnnotationContext", ["annotation", "group"])


class TestAnnotationHiddenFormatter(object):
    def test_preload_sets_founds_hidden_annotations_to_true(
        self, annotations, formatter
    ):
        annotation_ids = [a.id for a in annotations["hidden"]]

        expected = {id_: True for id_ in annotation_ids}
        assert formatter.preload(annotation_ids) == expected

    def test_preload_sets_missing_flags_to_false(self, annotations, formatter):
        annotation_ids = [a.id for a in annotations["public"]]

        expected = {id_: False for id_ in annotation_ids}
        assert formatter.preload(annotation_ids) == expected

    @pytest.fixture
    def annotations(self, factories):
        hidden = [
            mod.annotation for mod in factories.AnnotationModeration.create_batch(3)
        ]
        public = factories.Annotation.create_batch(2)
        return {"hidden": hidden, "public": public}


class TestAnonymousUserHiding(object):
    """An anonymous user will see redacted annotations when they're hidden."""

    def test_format_for_unhidden_annotation(self, formatter, annotation, group):
        resource = FakeAnnotationContext(annotation, group)
        assert formatter.format(resource) == {"hidden": False}

    def test_format_for_hidden_annotation(self, formatter, hidden_annotation, group):
        resource = FakeAnnotationContext(hidden_annotation, group)

        censored = {"hidden": True, "text": "", "tags": []}
        assert formatter.format(resource) == censored

    @pytest.fixture
    def current_user(self):
        return None


class TestNonAuthorHiding(object):
    """Regular users see redacted annotations, unless they are a moderator."""

    def test_format_for_unhidden_annotation(self, formatter, annotation, group):
        resource = FakeAnnotationContext(annotation, group)
        assert formatter.format(resource) == {"hidden": False}

    def test_format_for_non_moderator(self, formatter, hidden_annotation, group):
        resource = FakeAnnotationContext(hidden_annotation, group)

        censored = {"hidden": True, "text": "", "tags": []}
        assert formatter.format(resource) == censored

    def test_format_for_moderator(self, formatter, hidden_annotation, moderated_group):
        resource = FakeAnnotationContext(hidden_annotation, moderated_group)
        assert formatter.format(resource) == {"hidden": True}


class TestAuthorHiding(object):
    """The author usually does not see their annotations have been hidden.

    The one exception is when they are also a moderator for the group.
    """

    def test_format_for_public_annotation(self, formatter, annotation, group):
        resource = FakeAnnotationContext(annotation, group)
        assert formatter.format(resource) == {"hidden": False}

    def test_format_for_non_moderator(self, formatter, hidden_annotation, group):
        resource = FakeAnnotationContext(hidden_annotation, group)
        assert formatter.format(resource) == {"hidden": False}

    def test_format_for_moderator(self, formatter, hidden_annotation, moderated_group):
        resource = FakeAnnotationContext(hidden_annotation, moderated_group)
        assert formatter.format(resource) == {"hidden": True}

    @pytest.fixture
    def annotation(self, factories, current_user):
        return factories.Annotation(userid=current_user.userid)

    @pytest.fixture
    def hidden_annotation(self, factories, annotation):
        factories.AnnotationModeration(annotation=annotation)
        return annotation


@pytest.fixture
def current_user(factories):
    return factories.User()


@pytest.fixture
def formatter(moderation_svc, moderator_check, current_user):
    return AnnotationHiddenFormatter(moderation_svc, moderator_check, current_user)


@pytest.fixture
def moderation_svc(db_session):
    return AnnotationModerationService(db_session)


@pytest.fixture
def moderator_check(moderated_group):
    return lambda group: (group == moderated_group)


@pytest.fixture
def moderated_group(factories):
    return factories.Group()


@pytest.fixture
def group(factories):
    return factories.Group()


@pytest.fixture
def annotation(factories):
    return factories.Annotation()


@pytest.fixture
def hidden_annotation(factories):
    mod = factories.AnnotationModeration()
    return mod.annotation
