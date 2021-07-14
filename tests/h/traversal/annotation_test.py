from unittest import mock

import pyramid.security
import pytest
from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy

from h.security.permissions import Permission
from h.traversal import AnnotationContext, AnnotationRoot


class FakeGroup:
    # NB: Tests that use this do not validate that the principals are correct
    # for the indicated group. They validate that those principals are being
    # transferred over to the annotation as expected
    # As such, this has sort of a partial and wonky re-implementation of
    # ``h.models.Group.__acl__``
    # This is a symptom of the disease that is splitting ACL concerns between
    # traversal/resources and model classes
    # TODO: Refactor once we're able to move ACLs off of models
    def __init__(self, principals):
        acl = []
        for p in principals:
            acl.append((security.Allow, p, Permission.Group.READ))
            if p == security.Everyone:
                acl.append(
                    (security.Allow, security.Authenticated, Permission.Group.FLAG)
                )
                acl.append(
                    (security.Allow, security.Authenticated, Permission.Group.MODERATE)
                )
            else:
                acl.append((security.Allow, p, Permission.Group.FLAG))
                # Normally, the ``moderate`` permission would only be applied
                # to the admin (creator) of a group, but this ``FakeGroup``
                # is indeed fake. Tests in this module are merely around whether
                # this permission is translated appropriately from a group
                # to an annotation context (i.e. it should not be applied
                # to private annotations)
                acl.append((security.Allow, p, Permission.Group.MODERATE))
        self.__acl__ = acl


@pytest.mark.usefixtures("groupfinder_service", "links_service")
class TestAnnotationRoot:
    def test_it_does_not_assign_create_permission_without_authenticated_user(
        self, set_permissions, pyramid_request
    ):
        set_permissions()

        context = AnnotationRoot(pyramid_request)

        assert not pyramid_request.has_permission(Permission.Annotation.CREATE, context)

    def test_it_assigns_create_permission_to_authenticated_request(
        self, set_permissions, pyramid_request
    ):
        set_permissions(
            "acct:adminuser@foo", principals=[pyramid.security.Authenticated]
        )

        context = AnnotationRoot(pyramid_request)

        assert pyramid_request.has_permission(Permission.Annotation.CREATE, context)

    def test_get_item_fetches_annotation(self, pyramid_request, storage):
        factory = AnnotationRoot(pyramid_request)

        factory["123"]
        storage.fetch_annotation.assert_called_once_with(pyramid_request.db, "123")

    def test_get_item_returns_annotation_resource(self, pyramid_request, storage):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory["123"]
        assert isinstance(resource, AnnotationContext)

    def test_get_item_resource_has_right_annotation(self, pyramid_request, storage):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory["123"]
        assert resource.annotation == storage.fetch_annotation.return_value

    def test_get_item_raises_when_annotation_is_not_found(
        self, storage, pyramid_request
    ):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = None

        with pytest.raises(KeyError):
            factory["123"]

    def test_get_item_has_right_group_service(
        self, pyramid_request, storage, groupfinder_service
    ):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory["123"]
        assert resource.group_service == groupfinder_service

    def test_get_item_has_right_links_service(
        self, pyramid_request, storage, links_service
    ):
        factory = AnnotationRoot(pyramid_request)
        storage.fetch_annotation.return_value = mock.Mock()

        resource = factory["123"]
        assert resource.links_service == links_service

    @pytest.fixture
    def storage(self, patch):
        return patch("h.traversal.annotation.storage")


@pytest.mark.usefixtures("groupfinder_service", "links_service")
class TestAnnotationContext:
    def test_links(self, groupfinder_service, links_service):
        ann = mock.Mock()
        res = AnnotationContext(ann, groupfinder_service, links_service)

        result = res.links

        links_service.get_all.assert_called_once_with(ann)
        assert result == links_service.get_all.return_value

    def test_link(self, groupfinder_service, links_service):
        ann = mock.Mock()
        res = AnnotationContext(ann, groupfinder_service, links_service)

        result = res.link("json")

        links_service.get.assert_called_once_with(ann, "json")
        assert result == links_service.get.return_value

    def test_acl_private(self, factories, groupfinder_service, links_service):
        ann = factories.Annotation(shared=False, userid="saoirse")
        res = AnnotationContext(ann, groupfinder_service, links_service)
        actual = res.__acl__()
        # Note NOT the ``moderate`` permission
        expect = [
            (security.Allow, "saoirse", Permission.Annotation.READ),
            (security.Allow, "saoirse", Permission.Annotation.FLAG),
            (security.Allow, "saoirse", Permission.Annotation.UPDATE),
            (security.Allow, "saoirse", Permission.Annotation.DELETE),
            security.DENY_ALL,
        ]
        assert actual == expect

    def test_acl_shared_admin_perms(
        self, factories, groupfinder_service, links_service
    ):
        """
        Shared annotation contexts should still only give admin/update/delete
        permissions to the owner.
        """
        policy = ACLAuthorizationPolicy()

        ann = factories.Annotation(shared=False, userid="saoirse")
        res = AnnotationContext(ann, groupfinder_service, links_service)

        for perm in [
            Permission.Annotation.UPDATE,
            Permission.Annotation.DELETE,
        ]:
            assert policy.permits(res, ["saoirse"], perm)
            assert not policy.permits(res, ["someoneelse"], perm)

    def test_acl_deleted(self, factories, groupfinder_service, links_service):
        """
        Nobody -- not even the owner -- should have any permissions on a
        deleted annotation.
        """
        policy = ACLAuthorizationPolicy()

        ann = factories.Annotation(userid="saoirse", deleted=True)
        res = AnnotationContext(ann, groupfinder_service, links_service)

        for perm in [
            Permission.Annotation.READ,
            Permission.Annotation.UPDATE,
            Permission.Annotation.DELETE,
            Permission.Annotation.MODERATE,
        ]:
            assert not policy.permits(res, ["saiorse"], perm)

    @pytest.mark.parametrize(
        "groupid,userid,permitted",
        [
            ("freeforall", "jim", True),
            ("freeforall", "saoirse", True),
            ("freeforall", None, True),
            ("only-saoirse", "jim", False),
            ("only-saoirse", "saoirse", True),
            ("only-saoirse", None, False),
            ("pals", "jim", True),
            ("pals", "saoirse", True),
            ("pals", "francis", False),
            ("pals", None, False),
            ("unknown-group", "jim", False),
            ("unknown-group", "saoirse", False),
            ("unknown-group", "francis", False),
            ("unknown-group", None, False),
        ],
    )
    def test_acl_read_shared(
        self,
        factories,
        pyramid_config,
        pyramid_request,
        groupid,
        userid,
        permitted,
        groupfinder_service,
        links_service,
    ):
        """
        Shared annotation contexts should delegate their 'read' permission to
        their containing group.
        """
        # Set up the test with a dummy authn policy and a real ACL authz
        # policy:
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(userid)
        pyramid_config.set_authorization_policy(policy)

        ann = factories.Annotation(shared=True, userid="mioara", groupid=groupid)
        res = AnnotationContext(ann, groupfinder_service, links_service)

        if permitted:
            assert pyramid_request.has_permission(Permission.Annotation.READ, res)
        else:
            assert not pyramid_request.has_permission(Permission.Annotation.READ, res)

    @pytest.mark.parametrize(
        "groupid,userid,permitted",
        [
            ("freeforall", "jim", True),
            ("freeforall", "saoirse", True),
            ("freeforall", None, False),
            ("only-saoirse", "jim", False),
            ("only-saoirse", "saoirse", True),
            ("only-saoirse", None, False),
            ("pals", "jim", True),
            ("pals", "saoirse", True),
            ("pals", "francis", False),
            ("pals", None, False),
            ("unknown-group", "jim", False),
            ("unknown-group", "saoirse", False),
            ("unknown-group", "francis", False),
            ("unknown-group", None, False),
        ],
    )
    def test_acl_flag_shared(
        self,
        factories,
        pyramid_config,
        pyramid_request,
        groupid,
        userid,
        permitted,
        groupfinder_service,
        links_service,
    ):
        """
        Flag permissions should echo read permissions with the exception that
        `Security.Everyone` does not get the permission
        """
        # Set up the test with a dummy authn policy and a real ACL authz
        # policy:
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(userid)
        pyramid_config.set_authorization_policy(policy)

        ann = factories.Annotation(shared=True, userid="mioara", groupid=groupid)
        res = AnnotationContext(ann, groupfinder_service, links_service)

        if permitted:
            assert pyramid_request.has_permission(Permission.Annotation.FLAG, res)
        else:
            assert not pyramid_request.has_permission(Permission.Annotation.FLAG, res)

    @pytest.mark.parametrize(
        "groupid,userid,permitted",
        [
            ("freeforall", "jim", True),
            ("freeforall", "saoirse", True),
            ("freeforall", None, False),
            ("only-saoirse", "jim", False),
            ("only-saoirse", "saoirse", True),
            ("only-saoirse", None, False),
            ("pals", "jim", True),
            ("pals", "saoirse", True),
            ("pals", "francis", False),
            ("pals", None, False),
            ("unknown-group", "jim", False),
            ("unknown-group", "saoirse", False),
            ("unknown-group", "francis", False),
            ("unknown-group", None, False),
        ],
    )
    def test_acl_moderate_shared(
        self,
        factories,
        pyramid_config,
        pyramid_request,
        groupid,
        userid,
        permitted,
        groupfinder_service,
        links_service,
    ):
        """
        Moderate permissions should only be applied when an annotation
        is shared—as the annotation here is shared, anyone set as a principal
        for the given ``FakeGroup`` will receive the ``moderate`` permission.
        """
        # Set up the test with a dummy authn policy and a real ACL authz
        # policy:
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(userid)
        pyramid_config.set_authorization_policy(policy)

        ann = factories.Annotation(shared=True, userid="mioara", groupid=groupid)
        res = AnnotationContext(ann, groupfinder_service, links_service)

        if permitted:
            assert pyramid_request.has_permission(Permission.Annotation.MODERATE, res)
        else:
            assert not pyramid_request.has_permission(
                Permission.Annotation.MODERATE, res
            )

    @pytest.fixture
    def groups(self):
        return {
            "freeforall": FakeGroup([security.Everyone]),
            "only-saoirse": FakeGroup(["saoirse"]),
            "pals": FakeGroup(["saoirse", "jim"]),
        }

    @pytest.fixture
    def groupfinder_service(self, groupfinder_service, groups):
        groupfinder_service.find.side_effect = lambda groupid: groups.get(groupid)

        return groupfinder_service
