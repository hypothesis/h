# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
import mock
from pyramid import security
from pyramid.authorization import ACLAuthorizationPolicy

from h.auth import role
from h.models import Organization
from h.services.group_links import GroupLinksService
from h.traversal.contexts import AnnotationContext
from h.traversal.contexts import GroupContext
from h.traversal.contexts import GroupUpsertContext
from h.traversal.contexts import OrganizationContext


@pytest.mark.usefixtures("group_service", "links_service")
class TestAnnotationContext(object):
    def test_links(self, group_service, links_service):
        ann = mock.Mock()
        res = AnnotationContext(ann, group_service, links_service)

        result = res.links

        links_service.get_all.assert_called_once_with(ann)
        assert result == links_service.get_all.return_value

    def test_link(self, group_service, links_service):
        ann = mock.Mock()
        res = AnnotationContext(ann, group_service, links_service)

        result = res.link("json")

        links_service.get.assert_called_once_with(ann, "json")
        assert result == links_service.get.return_value

    def test_acl_private(self, factories, group_service, links_service):
        ann = factories.Annotation(shared=False, userid="saoirse")
        res = AnnotationContext(ann, group_service, links_service)
        actual = res.__acl__()
        # Note NOT the ``moderate`` permission
        expect = [
            (security.Allow, "saoirse", "read"),
            (security.Allow, "saoirse", "flag"),
            (security.Allow, "saoirse", "admin"),
            (security.Allow, "saoirse", "update"),
            (security.Allow, "saoirse", "delete"),
            security.DENY_ALL,
        ]
        assert actual == expect

    def test_acl_shared_admin_perms(self, factories, group_service, links_service):
        """
        Shared annotation contexts should still only give admin/update/delete
        permissions to the owner.
        """
        policy = ACLAuthorizationPolicy()

        ann = factories.Annotation(shared=False, userid="saoirse")
        res = AnnotationContext(ann, group_service, links_service)

        for perm in ["admin", "update", "delete"]:
            assert policy.permits(res, ["saoirse"], perm)
            assert not policy.permits(res, ["someoneelse"], perm)

    def test_acl_deleted(self, factories, group_service, links_service):
        """
        Nobody -- not even the owner -- should have any permissions on a
        deleted annotation.
        """
        policy = ACLAuthorizationPolicy()

        ann = factories.Annotation(userid="saoirse", deleted=True)
        res = AnnotationContext(ann, group_service, links_service)

        for perm in ["read", "admin", "update", "delete", "moderate"]:
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
        group_service,
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
        res = AnnotationContext(ann, group_service, links_service)

        if permitted:
            assert pyramid_request.has_permission("read", res)
        else:
            assert not pyramid_request.has_permission("read", res)

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
        group_service,
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
        res = AnnotationContext(ann, group_service, links_service)

        if permitted:
            assert pyramid_request.has_permission("flag", res)
        else:
            assert not pyramid_request.has_permission("flag", res)

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
        group_service,
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
        res = AnnotationContext(ann, group_service, links_service)

        if permitted:
            assert pyramid_request.has_permission("moderate", res)
        else:
            assert not pyramid_request.has_permission("moderate", res)

    @pytest.fixture
    def groups(self):
        return {
            "freeforall": FakeGroup([security.Everyone]),
            "only-saoirse": FakeGroup(["saoirse"]),
            "pals": FakeGroup(["saoirse", "jim"]),
        }

    @pytest.fixture
    def group_service(self, pyramid_config, groups):
        group_service = mock.Mock(spec_set=["find"])
        group_service.find.side_effect = lambda groupid: groups.get(groupid)
        pyramid_config.register_service(
            group_service, iface="h.interfaces.IGroupService"
        )
        return group_service

    @pytest.fixture
    def links_service(self, pyramid_config):
        service = mock.Mock(spec_set=["get", "get_all"])
        pyramid_config.register_service(service, name="links")
        return service


@pytest.mark.usefixtures("links_svc")
class TestGroupContext(object):
    def test_it_returns_group_model_as_property(self, factories, pyramid_request):
        group = factories.Group()

        group_context = GroupContext(group, pyramid_request)

        assert group_context.group == group

    def test_it_proxies_links_to_svc(self, factories, links_svc, pyramid_request):
        group = factories.Group()

        group_context = GroupContext(group, pyramid_request)

        assert group_context.links == links_svc.get_all.return_value

    def test_it_returns_pubid_as_id(self, factories, pyramid_request):
        group = factories.Group()

        group_context = GroupContext(group, pyramid_request)

        assert group_context.id == group.pubid  # NOT the group.id

    def test_organization_is_None_if_the_group_has_no_organization(
        self, factories, pyramid_request
    ):
        group = factories.Group()

        group_context = GroupContext(group, pyramid_request)

        assert group_context.organization is None

    def test_it_expands_organization_if_the_group_has_one(
        self, factories, pyramid_request
    ):
        organization = factories.Organization()
        group = factories.Group(organization=organization)

        group_context = GroupContext(group, pyramid_request)

        assert group_context.organization.organization == organization

    def test_it_returns_None_for_missing_organization_relation(
        self, factories, pyramid_request
    ):
        group = factories.Group()
        group.organization = None

        group_context = GroupContext(group, pyramid_request)

        assert group_context.organization is None


@pytest.mark.usefixtures("organization_routes")
class TestOrganizationContext(object):
    def test_it_returns_organization_model_as_property(
        self, factories, pyramid_request
    ):
        organization = factories.Organization()

        organization_context = OrganizationContext(organization, pyramid_request)

        assert organization_context.organization == organization

    def test_it_returns_pubid_as_id(self, factories, pyramid_request):
        organization = factories.Organization()

        organization_context = OrganizationContext(organization, pyramid_request)

        assert organization_context.id != organization.id
        assert organization_context.id == organization.pubid

    def test_it_returns_links_property(self, factories, pyramid_request):
        organization = factories.Organization()

        organization_context = OrganizationContext(organization, pyramid_request)

        assert organization_context.links == {}

    def test_it_returns_logo_property_as_route_url(self, factories, pyramid_request):
        fake_logo = "<svg>H</svg>"
        pyramid_request.route_url = mock.Mock()

        organization = factories.Organization(logo=fake_logo)

        organization_context = OrganizationContext(organization, pyramid_request)
        logo = organization_context.logo

        pyramid_request.route_url.assert_called_with(
            "organization_logo", pubid=organization.pubid
        )
        assert logo is not None

    def test_it_returns_none_for_logo_if_no_logo(self, factories, pyramid_request):
        pyramid_request.route_url = mock.Mock()

        organization = factories.Organization(logo=None)

        organization_context = OrganizationContext(organization, pyramid_request)
        logo = organization_context.logo

        pyramid_request.route_url.assert_not_called
        assert logo is None

    def test_default_property_if_not_default_organization(
        self, factories, pyramid_request
    ):
        organization = factories.Organization()

        organization_context = OrganizationContext(organization, pyramid_request)

        assert organization_context.default is False

    def test_default_property_if_default_organization(self, factories, pyramid_request):
        organization = Organization.default(pyramid_request.db)

        organization_context = OrganizationContext(organization, pyramid_request)

        assert organization_context.default is True


@pytest.mark.usefixtures("links_svc")
class TestGroupUpsertContext(object):
    def test_acl_applies_root_upsert_to_user_role_when_no_group(
        self, pyramid_config, pyramid_request
    ):
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(
            "acct:adminuser@foo", groupids=[security.Authenticated, role.User]
        )
        pyramid_config.set_authorization_policy(policy)

        context = GroupUpsertContext(group=None, request=pyramid_request)

        assert pyramid_request.has_permission("upsert", context)

    def test_acl_denies_root_upsert_if_no_user_role_and_no_group(
        self, pyramid_config, pyramid_request
    ):
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(
            "acct:adminuser@foo", groupids=[security.Authenticated]
        )
        pyramid_config.set_authorization_policy(policy)

        context = GroupUpsertContext(group=None, request=pyramid_request)

        assert not pyramid_request.has_permission("upsert", context)

    def test_acl_applies_group_model_acl_if_group_is_not_None(
        self, pyramid_config, pyramid_request, factories
    ):
        group = factories.Group()
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(
            "acct:adminuser@foo", groupids=[security.Authenticated]
        )
        pyramid_config.set_authorization_policy(policy)

        context = GroupUpsertContext(group=group, request=pyramid_request)

        assert context.__acl__() == group.__acl__()

    def test_acl_does_not_apply_root_upsert_permission_if_group_is_not_None(
        self, pyramid_config, pyramid_request, factories
    ):
        group = factories.Group()
        policy = ACLAuthorizationPolicy()
        pyramid_config.testing_securitypolicy(
            "acct:adminuser@foo", groupids=[security.Authenticated, role.User]
        )
        pyramid_config.set_authorization_policy(policy)

        context = GroupUpsertContext(group=group, request=pyramid_request)

        # an `upsert` permission could be present in the ACL via the model IF the current
        # user were the creator, but they're not
        assert not pyramid_request.has_permission("upsert", context)


class FakeGroup(object):
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
            acl.append((security.Allow, p, "read"))
            if p == security.Everyone:
                acl.append((security.Allow, security.Authenticated, "flag"))
                acl.append((security.Allow, security.Authenticated, "moderate"))
            else:
                acl.append((security.Allow, p, "flag"))
                # Normally, the ``moderate`` permission would only be applied
                # to the admin (creator) of a group, but this ``FakeGroup``
                # is indeed fake. Tests in this module are merely around whether
                # this permission is translated appropriately from a group
                # to an annotation context (i.e. it should not be applied
                # to private annotations)
                acl.append((security.Allow, p, "moderate"))
        self.__acl__ = acl


@pytest.fixture
def links_svc(pyramid_config):
    svc = mock.create_autospec(GroupLinksService, spec_set=True, instance=True)
    pyramid_config.register_service(svc, name="group_links")
    return svc


@pytest.fixture
def organization_routes(pyramid_config):
    pyramid_config.add_route("organization_logo", "/organization/{pubid}/logo")
