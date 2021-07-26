import pytest

__all__ = ("group", "other_authority_group", "open_group", "user_owned_group")


@pytest.fixture
def group(factories, db_session):
    # Readable by members, writable by members and joinable by authority
    group = factories.Group()
    db_session.commit()

    return group


@pytest.fixture
def other_authority_group(factories, db_session):
    # Readable by members, writable by members and joinable by authority
    group = factories.Group(authority="different_authority")
    db_session.commit()

    return group


@pytest.fixture
def open_group(factories, db_session):
    # Readable by world, writeable by authority and joinable by None
    group = factories.OpenGroup()
    db_session.commit()

    return group


@pytest.fixture
def user_owned_group(factories, db_session, user):
    # Readable by members, writable by members and joinable by authority
    group = factories.Group(creator=user)
    db_session.commit()

    return group
