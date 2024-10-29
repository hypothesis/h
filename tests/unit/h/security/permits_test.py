from unittest.mock import patch, sentinel

import pytest
from pyramid.security import Allowed, Denied

from h.models import GroupMembership
from h.security import Identity, Permission
from h.security.permits import PERMISSION_MAP, identity_permits
from h.traversal import AnnotationContext


def always_true(_identity, _context):
    return True


def always_false(_identity, _context):
    return False


def explode(_identity, _context):
    assert False, "This should not be reached"  # pragma: no cover


class TestIdentityPermits:
    # We aren't going to test the contents of the mapping, all we could really
    # do there is copy it here. What we will do is test that the mechanism
    # works
    @pytest.mark.parametrize(
        "clauses,grants",
        (
            # At least one clause must be true, so if there are none, it's false
            ([], Denied("Denied")),
            # A clause requires each element in it to be true
            ([[always_true]], Allowed("Allowed")),
            ([[always_false]], Denied("Denied")),
            ([[always_true, always_true]], Allowed("Allowed")),
            ([[always_true, always_true, always_false]], Denied("Denied")),
            # An empty clause is always true
            ([[]], Allowed("Allowed")),
            # We lazy evaluate, so if anything in a clause is false we don't
            # evaluate predicates beyond it
            ([[always_false, explode]], Denied("Denied")),
            # Only one clause has to be true
            ([[always_false], [always_true]], Allowed("Allowed")),
            ([[always_true], [always_false]], Allowed("Allowed")),
            ([[always_true], [explode]], Allowed("Allowed")),
        ),
    )
    def test_it(self, PERMISSION_MAP, clauses, grants):
        PERMISSION_MAP[sentinel.permission] = clauses

        result = identity_permits(
            sentinel.identity, sentinel.context, sentinel.permission
        )

        assert result == grants

    def test_it_denies_with_missing_permission(self):
        assert identity_permits(
            sentinel.identity, sentinel.context, sentinel.non_existent_permission
        ) == Denied("Denied")

    @pytest.fixture(autouse=True)
    def PERMISSION_MAP(self):
        with patch.dict(PERMISSION_MAP, {}) as mapping:
            yield mapping


class TestIdentityPermitsIntegrated:
    def test_it(self, user, group, annotation):
        # We aren't going to go bonkers here, but a couple of tests to show
        # this actually holds together. This isn't really to inform us of any
        # particular failure, but just give us sensitivity if this doesn't work
        # at all when you hook it together for real.

        identity = Identity.from_models(user=user)
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
        assert not identity_permits(identity, None, Permission.AdminPage.HIGH_RISK)
        identity.user.admin = True
        assert identity_permits(identity, None, Permission.AdminPage.HIGH_RISK)

    @pytest.fixture
    def user(self, factories, group):
        return factories.User(memberships=[GroupMembership(group=group)])

    @pytest.fixture
    def group(self, factories):
        return factories.Group()

    @pytest.fixture
    def annotation(self, factories, group, user):
        return factories.Annotation(group=group, userid=user.userid, shared=True)
