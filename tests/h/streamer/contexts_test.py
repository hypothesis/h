import pytest
from h_matchers import Any
from pyramid.security import DENY_ALL

from h.streamer.contexts import AnnotationNotificationContext


class TestAnnotationNotificationContext:
    def test_public_annotation_permissions(self, get_context_acl, factories):
        acl = get_context_acl(factories.Annotation(shared=True))

        assert acl[0] == ("Allow", "system.Everyone", "read")

    def test_private_annotation_permissions(self, get_context_acl, factories):
        annotation = factories.Annotation(shared=False)
        acl = get_context_acl(annotation)

        assert acl[0] == ("Allow", annotation.userid, "read")

    def test_deleted_still_returns_read_permissions(self, get_context_acl, factories):
        acl = get_context_acl(factories.Annotation(deleted=True))

        assert acl[0] == ("Allow", Any.string(), "read")

    def test_it_always_adds_deny_last(self, get_context_acl, factories):
        acl = get_context_acl(factories.Annotation())

        assert acl[-1] == DENY_ALL

    @pytest.fixture
    def get_context_acl(self, db_session, groupfinder_service):
        def get_context(annotation):
            context = AnnotationNotificationContext(
                annotation, group_service=groupfinder_service, links_service=None
            )

            return context.__acl__()

        return get_context
