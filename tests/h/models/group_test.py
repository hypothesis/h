import pytest

from h import models
from h.models.group import AUTHORITY_PROVIDED_ID_MAX_LENGTH, ReadableBy, WriteableBy


def test_init_sets_given_attributes():
    group = models.Group(name="My group", authority="example.com", enforce_scope=False)

    assert group.name == "My group"
    assert group.authority == "example.com"
    assert not group.enforce_scope


def test_with_short_name():
    """Should raise ValueError if name shorter than 3 characters."""
    with pytest.raises(ValueError):
        models.Group(name="ab")


def test_with_long_name():
    """Should raise ValueError if name longer than 25 characters."""
    with pytest.raises(ValueError):
        models.Group(name="abcdefghijklmnopqrstuvwxyz")


def test_enforce_scope_is_True_by_default(db_session, factories):
    user = factories.User()
    group = models.Group(name="Foobar", authority="foobar.com", creator=user)

    db_session.add(group)
    db_session.flush()

    assert group.enforce_scope is True


def test_enforce_scope_can_be_set_False(db_session, factories):
    user = factories.User()
    group = models.Group(
        name="Foobar", authority="foobar.com", creator=user, enforce_scope=False
    )

    db_session.add(group)
    db_session.flush()

    assert not group.enforce_scope


def test_slug(db_session, factories, organization):
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(
        name=name,
        authority="foobar.com",
        creator=user,
        organization=organization,
    )
    db_session.add(group)
    db_session.flush()

    assert group.slug == "my-hypothesis-group"


def test_type_returns_open_for_open_groups(factories):
    assert factories.OpenGroup().type == "open"


def test_type_returns_private_for_private_groups(factories):
    assert factories.Group().type == "private"


def test_type_returns_restricted_for_restricted_groups(factories):
    assert factories.RestrictedGroup().type == "restricted"


def test_it_returns_None_by_default_for_authority_provided_id():
    group = models.Group(name="abcdefg")

    assert group.authority_provided_id is None


def test_it_returns_None_for_groupid_if_authority_provided_id_is_None(factories):
    group = factories.Group(authority_provided_id=None)

    assert group.groupid is None


def test_it_returns_formatted_groupid_if_authority_provided_id(factories):
    group = factories.Group()
    group.authority_provided_id = "hithere"

    assert group.groupid == f"group:hithere@{group.authority}"


def test_groupid_setter_raises_ValueError_if_groupid_invalid(factories):
    group = factories.Group()

    with pytest.raises(ValueError, match="isn't a valid groupid"):
        group.groupid = "nonsense"


def test_groupid_setter_sets_consistuent_fields(factories):
    group = factories.Group()
    group.groupid = "group:onetwo@threefour.com"

    assert group.authority_provided_id == "onetwo"
    assert group.authority == "threefour.com"


def test_groupid_setter_accepts_None_and_nullifies_authority_provided_id(factories):
    group = factories.Group()
    group.groupid = "group:onetwo@threefour.com"
    group.groupid = None

    assert group.groupid is None
    assert group.authority == "threefour.com"
    assert group.authority_provided_id is None


@pytest.mark.parametrize(
    "authority_provided_id", ["%%&whatever", "^flop", "#---", "ßeta"]
)
def test_it_raises_ValueError_if_invalid_authority_provided_id(authority_provided_id):
    group = models.Group(name="abcdefg")

    with pytest.raises(ValueError, match="authority_provided_id must only contain"):
        group.authority_provided_id = authority_provided_id


def test_it_raises_ValueError_if_authority_provided_id_too_long():
    group = models.Group(name="abcdefg")

    with pytest.raises(ValueError, match="characters or fewer"):
        group.authority_provided_id = "a" * (AUTHORITY_PROVIDED_ID_MAX_LENGTH + 1)


def test_it_allows_authority_provided_id_to_be_None():
    group = models.Group(name="abcdefg")

    group.authority_provided_id = None


def test_type_raises_for_unknown_type_of_group(factories):
    group = factories.Group()
    # Set the group's access flags to an invalid / unused combination.
    group.joinable_by = None
    group.readable_by = ReadableBy.members
    group.writeable_by = WriteableBy.authority

    expected_err = "^This group doesn't seem to match any known type"
    with pytest.raises(ValueError, match=expected_err):
        _ = group.type


def test_you_cannot_set_type(factories):
    group = factories.Group()

    with pytest.raises(AttributeError, match="can't set attribute"):
        group.type = "open"


def test_repr(db_session, factories, organization):
    name = "My Hypothesis Group"
    user = factories.User()

    group = models.Group(
        name=name,
        authority="foobar.com",
        creator=user,
        organization=organization,
    )
    db_session.add(group)
    db_session.flush()

    assert repr(group) == "<Group: my-hypothesis-group>"


def test_group_organization(db_session):
    name = "My Hypothesis Group"

    org = models.Organization(name="My Organization", authority="foobar.com")
    db_session.add(org)
    db_session.flush()

    group = models.Group(name=name, authority="foobar.com", organization=org)
    db_session.add(group)
    db_session.flush()

    assert group.organization == org
    assert group.organization_id == org.id


def test_created_by(db_session, factories, organization):
    name_1 = "My first group"
    name_2 = "My second group"
    user = factories.User()

    group_1 = models.Group(
        name=name_1,
        authority="foobar.com",
        creator=user,
        organization=organization,
    )
    group_2 = models.Group(
        name=name_2,
        authority="foobar.com",
        creator=user,
        organization=organization,
    )

    db_session.add_all([group_1, group_2])
    db_session.flush()

    assert models.Group.created_by(db_session, user).all() == [group_1, group_2]


def test_public_group():
    group = models.Group(readable_by=ReadableBy.world)

    assert group.is_public


def test_non_public_group():
    group = models.Group(readable_by=ReadableBy.members)

    assert not group.is_public


@pytest.fixture()
def organization(factories):
    return factories.Organization()
