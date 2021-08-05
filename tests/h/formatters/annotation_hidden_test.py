from unittest.mock import create_autospec

import pytest

from h.formatters.annotation_hidden import AnnotationHiddenFormatter
from h.security.permissions import Permission
from h.services.annotation_moderation import AnnotationModerationService


class TestAnnotationHiddenFormatter:
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


class TestAnonymousUserHiding:
    """An anonymous user will see redacted annotations when they're hidden."""

    def test_format_for_unhidden_annotation(self, formatter, annotation):
        assert formatter.format(annotation) == {"hidden": False}

    def test_format_for_hidden_annotation(self, formatter, hidden_annotation):

        censored = {"hidden": True, "text": "", "tags": []}
        assert formatter.format(hidden_annotation) == censored

    @pytest.fixture
    def current_user(self):
        return None


class TestNonAuthorHiding:
    """Regular users see redacted annotations, unless they are a moderator."""

    def test_format_for_unhidden_annotation(self, formatter, annotation):
        assert formatter.format(annotation) == {"hidden": False}

    def test_format_for_non_moderator(self, formatter, hidden_annotation):
        assert formatter.format(hidden_annotation) == {
            "hidden": True,
            "text": "",
            "tags": [],
        }


class TestAuthorHiding:
    """
    The author usually does not see their annotations have been hidden.

    The one exception is when they are also a moderator for the group.
    """

    def test_format_for_public_annotation(self, formatter, annotation):
        assert formatter.format(annotation) == {"hidden": False}

    def test_format_for_non_moderator(self, formatter, hidden_annotation):
        assert formatter.format(hidden_annotation) == {"hidden": False}

    def test_format_for_moderator(
        self, formatter, hidden_annotation, has_permission, AnnotationContext
    ):
        has_permission.return_value = True

        assert formatter.format(hidden_annotation) == {"hidden": True}
        AnnotationContext.assert_called_once_with(hidden_annotation)
        has_permission.assert_called_once_with(
            Permission.Annotation.MODERATE, context=AnnotationContext.return_value
        )

    @pytest.fixture
    def annotation(self, factories, current_user):
        return factories.Annotation(userid=current_user.userid)

    @pytest.fixture
    def AnnotationContext(self, patch):
        return patch("h.formatters.annotation_hidden.AnnotationContext")


@pytest.fixture
def current_user(factories):
    return factories.User()


@pytest.fixture
def formatter(moderation_svc, has_permission, current_user):
    return AnnotationHiddenFormatter(moderation_svc, has_permission, current_user)


@pytest.fixture
def moderation_svc(db_session):
    # TODO! - This should be mocked - We are probably testing other code here
    return AnnotationModerationService(db_session)


@pytest.fixture
def has_permission(pyramid_request):
    return create_autospec(pyramid_request.has_permission, return_value=False)


@pytest.fixture
def annotation(factories):
    return factories.Annotation()


@pytest.fixture
def hidden_annotation(factories, annotation):
    factories.AnnotationModeration(annotation=annotation)
    return annotation
