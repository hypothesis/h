from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy

from h.security.permissions import Permission
from h.traversal import AnnotationContext, AnnotationRoot


class TestAnnotationRoot:
    def test_create_permission_requires_authenticated_user(self, root, permits):
        assert permits(root, [security.Authenticated], Permission.Annotation.CREATE)
        assert not permits(root, [], Permission.Annotation.CREATE)

    def test_annotation_lookup(
        self,
        root,
        pyramid_request,
        AnnotationContext,
        storage,
        groupfinder_service,
        links_service,
    ):
        context = root[sentinel.annotation_id]

        assert context == AnnotationContext.return_value
        storage.fetch_annotation.assert_called_once_with(
            pyramid_request.db, sentinel.annotation_id
        )
        AnnotationContext.assert_called_once_with(
            storage.fetch_annotation.return_value, groupfinder_service, links_service
        )

    def test_failing_annotation_lookup(self, root, storage):
        storage.fetch_annotation.return_value = None

        with pytest.raises(KeyError):
            assert root[sentinel.annotation_id]

    @pytest.fixture
    def root(self, pyramid_request):
        return AnnotationRoot(pyramid_request)

    @pytest.fixture
    def storage(self, patch):
        return patch("h.traversal.annotation.storage")

    @pytest.fixture
    def AnnotationContext(self, patch):
        return patch("h.traversal.annotation.AnnotationContext")


class TestAnnotationContext:
    def test_links(self, annotation, context, links_service):
        result = context.links

        links_service.get_all.assert_called_once_with(annotation)
        assert result == links_service.get_all.return_value

    def test_link(self, annotation, context, links_service):
        result = context.link("json")

        links_service.get.assert_called_once_with(annotation, "json")
        assert result == links_service.get.return_value

    def test_acl_everything_is_denied_when_deleted(self, annotation, context):
        annotation.deleted = True

        acl = context.__acl__()

        assert acl == [security.DENY_ALL]

    def test_acl_the_user_can_always_update_and_delete_their_own(
        self, annotation, context, permits
    ):
        permits(context, [annotation.userid], Permission.Annotation.UPDATE)
        permits(context, [annotation.userid], Permission.Annotation.DELETE)

    def test_acl_non_shared_permissions_go_to_the_user(
        self, annotation, context, permits
    ):
        annotation.shared = False

        permits(context, [annotation.userid], Permission.Annotation.READ)
        permits(context, [annotation.userid], Permission.Annotation.FLAG)

    def test_acl_shared_permissions_mirror_the_group(
        self, annotation, context, permits, groupfinder_service
    ):
        annotation.shared = True

        class GroupACLs:
            __acl__ = [
                (security.Allow, "principal_1", Permission.Group.FLAG),
                (security.Allow, "principal_2", Permission.Group.FLAG),
                (security.Allow, "principal_1", Permission.Group.MODERATE),
                (security.Allow, "principal_2", Permission.Group.MODERATE),
            ]

        groupfinder_service.find.return_value = GroupACLs()

        permits(context, ["principal_1"], Permission.Annotation.FLAG)
        permits(context, ["principal_2"], Permission.Annotation.FLAG)
        permits(context, ["principal_1"], Permission.Annotation.MODERATE)
        permits(context, ["principal_2"], Permission.Annotation.MODERATE)

    def test_acl_shared_permissions_with_no_group(
        self, annotation, context, permits, groupfinder_service
    ):
        annotation.shared = True
        groupfinder_service.find.return_value = None

        acl = context.__acl__()

        assert (security.Allow, Any(), Permission.Annotation.FLAG) not in acl
        assert (security.Allow, Any(), Permission.Annotation.MODERATE) not in acl

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation()

    @pytest.fixture
    def context(self, annotation, groupfinder_service, links_service):
        return AnnotationContext(annotation, groupfinder_service, links_service)


@pytest.fixture
def permits():
    def permits(context, principals, permission):
        return ACLAuthorizationPolicy().permits(context, principals, permission)

    return permits
