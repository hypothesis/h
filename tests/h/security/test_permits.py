from unittest.mock import sentinel

import pytest

from h.security import Identity, Permission
from h.security.permits import identity_permits
from h.traversal import AnnotationContext, Root


class TestIdentityPermits:
    def test_it(self, principals_for_identity, ACLAuthorizationPolicy):
        result = identity_permits(
            sentinel.identity, sentinel.context, sentinel.permission
        )

        principals_for_identity.assert_called_once_with(sentinel.identity)
        ACLAuthorizationPolicy.assert_called_once_with()
        ACLAuthorizationPolicy.return_value.permits.assert_called_once_with(
            context=sentinel.context,
            principals=principals_for_identity.return_value,
            permission=sentinel.permission,
        )
        assert result == ACLAuthorizationPolicy.return_value.permits.return_value

    @pytest.fixture
    def principals_for_identity(self, patch):
        return patch("h.security.permits.principals_for_identity")

    @pytest.fixture
    def ACLAuthorizationPolicy(self, patch):
        return patch("h.security.permits.ACLAuthorizationPolicy")


class TestIdentityPermitsIntegrated:
    def test_it(self, user, group, annotation):
        # We aren't going to go bonkers here, but a couple of tests to show
        # this actually holds together. This isn't really to inform us of any
        # particular failure, but just give us sensitivity if this doesn't work
        # at all when you hook it together for real.

        identity = Identity(user)
        anno_context = AnnotationContext(annotation=annotation)

        # A user can delete their own annotation
        assert identity_permits(identity, anno_context, Permission.Annotation.DELETE)

        # Once a user is the creator of a group they can moderate
        assert not identity_permits(
            identity, anno_context, Permission.Annotation.MODERATE
        )
        group.creator = user
        assert identity_permits(identity, anno_context, Permission.Annotation.MODERATE)

        # Once a user is an admin they can do admin things
        admin_context = Root(sentinel.request)
        assert not identity_permits(identity, admin_context, Permission.AdminPage.NIPSA)
        user.admin = True
        assert identity_permits(identity, admin_context, Permission.AdminPage.NIPSA)

        # We need the right context
        assert not identity_permits(identity, anno_context, Permission.AdminPage.NIPSA)

    @pytest.fixture
    def user(self, factories, group):
        return factories.User(groups=[group])

    @pytest.fixture
    def group(self, factories):
        return factories.Group()

    @pytest.fixture
    def annotation(self, factories, group, user):
        return factories.Annotation(group=group, userid=user.userid, shared=True)
