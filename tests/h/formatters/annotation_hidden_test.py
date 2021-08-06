from unittest.mock import create_autospec

import pytest
from h_matchers import Any

from h.formatters.annotation_hidden import AnnotationHiddenFormatter
from h.security.permissions import Permission
from h.traversal import AnnotationContext


class TestAnnotationHiddenFormatter:
    def test_it_hides_moderated(self, formatter, annotation):
        annotation.moderation = None

        assert formatter.format(annotation) == {"hidden": False}

    def test_the_author_can_see_it(self, formatter, annotation, user):
        annotation.user = user

        assert formatter.format(annotation) == {"hidden": False}

    def test_moderators_see_everything(self, formatter, annotation, has_permission):
        has_permission.return_value = True

        result = formatter.format(annotation)

        has_permission.assert_called_once_with(
            Permission.Annotation.MODERATE,
            Any.instance_of(AnnotationContext).with_attrs({"annotation": annotation}),
        )

        assert result == {"hidden": True}

    def test_others_see_it_hidden_and_censored(self, formatter, annotation):
        assert formatter.format(annotation) == {"hidden": True, "text": "", "tags": []}

    @pytest.fixture
    def has_permission(self, pyramid_request):
        return create_autospec(pyramid_request.has_permission, return_value=False)

    @pytest.fixture
    def annotation(self, factories):
        annotation = factories.Annotation.build()
        annotation.moderation = factories.AnnotationModeration.build()
        return annotation

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def formatter(self, has_permission, user):
        return AnnotationHiddenFormatter(has_permission, user)
