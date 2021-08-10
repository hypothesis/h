from unittest import mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from h.services.exceptions import ConflictError, ValidationError
from h.services.group_update import GroupUpdateService, group_update_factory


class TestGroupUpdate:
    def test_it_updates_valid_group_attrs(self, factories, svc):
        group = factories.Group()
        data = {"name": "foobar", "description": "I am foobar"}

        svc.update(group, **data)

        assert group.name == "foobar"
        assert group.description == "I am foobar"

    def test_it_returns_updated_group_model(self, factories, svc):
        group = factories.Group()
        data = {"name": "whatnot"}

        updated_group = svc.update(group, **data)

        assert updated_group == group

    def test_it_accepts_scope_relations(self, factories, svc):
        group = factories.Group()
        scopes = [factories.GroupScope(), factories.GroupScope()]
        data = {"name": "whatnot", "scopes": scopes}

        updated_group = svc.update(group, **data)

        assert updated_group.scopes == scopes

    def test_it_replaces_scope_relations(self, factories, svc):
        group = factories.Group(scopes=[factories.GroupScope()])
        updated_scopes = [factories.GroupScope(), factories.GroupScope()]
        data = {"name": "whatnot", "scopes": updated_scopes}

        updated_group = svc.update(group, **data)

        assert updated_group.scopes == updated_scopes

    def test_it_does_not_protect_against_undefined_properties(self, factories, svc):
        group = factories.Group()
        data = {"some_random_field": "whatever"}

        updated_group = svc.update(group, **data)

        # This won't be persisted in the DB, of course, but the model instance
        # doesn't have a problem with it
        assert updated_group.some_random_field == "whatever"

    def test_it_raises_ValidationError_if_name_fails_model_validation(
        self, factories, svc
    ):
        group = factories.Group()

        with pytest.raises(ValidationError, match="name must be between"):
            svc.update(group, name="ye")

    def test_it_raises_ValidationError_if_authority_provided_id_fails_model_validation(
        self, factories, svc
    ):
        group = factories.Group()

        with pytest.raises(
            ValidationError,
            match="must only contain characters allowed in encoded URIs",
        ):
            svc.update(group, authority_provided_id="%%^&#*")

    def test_it_raises_ConflictError_on_provided_id_uniqueness_violation(
        self, factories, svc
    ):
        factories.Group(authority_provided_id="foo", authority="foo.com")
        group2 = factories.Group(authority_provided_id="bar", authority="foo.com")

        with pytest.raises(ConflictError, match="authority_provided_id"):
            svc.update(group2, authority_provided_id="foo")

    def test_it_raises_on_any_other_SQLAlchemy_exception(self, factories):
        fake_session = mock.Mock()
        fake_session.flush.side_effect = SQLAlchemyError("foo")

        update_svc = GroupUpdateService(session=fake_session)
        group = factories.Group(authority_provided_id="foo", authority="foo.com")

        with pytest.raises(SQLAlchemyError):
            update_svc.update(group, name="fingers")


class TestFactory:
    def test_returns_group_update_service(self, pyramid_request):
        group_update_service = group_update_factory(None, pyramid_request)

        assert isinstance(group_update_service, GroupUpdateService)


@pytest.fixture
def svc(db_session):
    return GroupUpdateService(session=db_session)
