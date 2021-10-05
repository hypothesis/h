from datetime import datetime
from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.authorization import Everyone
from sqlalchemy import event

from h.security.permissions import Permission
from h.services.annotation_json import AnnotationJSONService, factory
from h.traversal import AnnotationContext


class TestAnnotationJSONService:
    def test_present(
        self, service, annotation, links_service, user_service, DocumentJSONPresenter
    ):
        annotation.created = datetime(2016, 2, 24, 18, 3, 25, 768)
        annotation.updated = datetime(2016, 2, 29, 10, 24, 5, 564)
        annotation.references = ["referenced-id-1", "referenced-id-2"]
        annotation.extra = {"extra-1": "foo", "extra-2": "bar"}

        result = service.present(annotation)

        links_service.get_all.assert_called_once_with(annotation)
        user_service.fetch.assert_called_once_with(annotation.userid)

        assert result == {
            "id": annotation.id,
            "created": "2016-02-24T18:03:25.000768+00:00",
            "updated": "2016-02-29T10:24:05.000564+00:00",
            "user": annotation.userid,
            "uri": annotation.target_uri,
            "group": annotation.groupid,
            "text": annotation.text,
            "tags": annotation.tags,
            "permissions": {
                "read": [annotation.userid],
                "admin": [annotation.userid],
                "update": [annotation.userid],
                "delete": [annotation.userid],
            },
            "target": annotation.target,
            "document": DocumentJSONPresenter.return_value.asdict.return_value,
            "links": links_service.get_all.return_value,
            "references": annotation.references,
            "extra-1": "foo",
            "extra-2": "bar",
            "user_info": {"display_name": user_service.fetch.return_value.display_name},
        }

        DocumentJSONPresenter.assert_called_once_with(annotation.document)
        DocumentJSONPresenter.return_value.asdict.assert_called_once_with()

    def test_present_without_references(self, service, annotation):
        annotation.references = None

        result = service.present(annotation)

        assert "references" not in result

    def test_present_extra_inherits_correctly(self, service, annotation):
        annotation.extra = {"id": "DIFFERENT"}

        presented = service.present(annotation)

        # We can't override things (we are applied first)
        assert presented["id"] == annotation.id
        # And we aren't mutated
        assert annotation.extra == {"id": "DIFFERENT"}

    @pytest.mark.parametrize(
        "shared,readable_by,permission_template",
        (
            (False, [], "{annotation.userid}"),
            (True, [], "group:{annotation.groupid}"),
            (True, [Everyone], "group:__world__"),
        ),
    )
    def test_present_read_permission(
        self,
        service,
        annotation,
        identity_permits,
        shared,
        readable_by,
        permission_template,
    ):
        annotation.shared = shared
        identity_permits.return_value = readable_by

        presented = service.present(annotation)

        permission = permission_template.format(annotation=annotation)
        assert presented["permissions"]["read"] == [permission]

    def test_present_skips_the_read_permission_check_if_group_is_world(
        self, service, annotation, identity_permits
    ):
        annotation.shared = True
        annotation.groupid = "__world__"

        presented = service.present(annotation)

        identity_permits.assert_not_called()
        assert presented["permissions"]["read"] == ["group:__world__"]

    def test_present_for_user(self, service, user, annotation, flag_service):
        result = service.present_for_user(annotation, user)

        flag_service.flagged.assert_called_once_with(user, annotation)
        flag_service.flag_count.assert_called_once_with(annotation)
        assert result == Any.dict.containing(
            {
                # At least one thing from normal serialization
                "id": Any(),
                # ... and the things this method adds
                "hidden": False,
                "flagged": flag_service.flagged.return_value,
                "moderation": {"flagCount": flag_service.flag_count.return_value},
            }
        )

    def test_present_for_user_only_shows_moderation_to_moderators(
        self, service, annotation, user, identity_permits, Identity
    ):
        identity_permits.return_value = False

        result = service.present_for_user(annotation, user)

        Identity.from_models.assert_called_once_with(user=user)
        identity_permits.assert_called_once_with(
            identity=Identity.from_models.return_value,
            context=Any.instance_of(AnnotationContext).with_attrs(
                {"annotation": annotation}
            ),
            permission=Permission.Annotation.MODERATE,
        )

        assert "moderation" not in result

    @pytest.mark.usefixtures("with_hidden_annotation")
    def test_present_for_user_hidden_status_is_not_shown_to_creator(
        self, service, annotation, user
    ):
        annotation.userid = user.userid

        result = service.present_for_user(annotation, user)

        assert not result["hidden"]

    @pytest.mark.usefixtures("with_hidden_annotation")
    def test_present_for_user_hidden_censors_content_for_normal_users(
        self, service, annotation, user, identity_permits
    ):
        identity_permits.return_value = False

        result = service.present_for_user(annotation, user)

        assert result["hidden"]
        assert not result["text"]
        assert not result["tags"]

    @pytest.mark.usefixtures("with_hidden_annotation")
    def test_present_for_user_hidden_shows_everything_to_moderators(
        self, service, annotation, user, identity_permits
    ):
        identity_permits.return_value = True

        result = service.present_for_user(annotation, user)

        assert result["hidden"]
        assert result["text"]
        assert result["tags"]

    def test_present_all_for_user(
        self, service, annotation, user, flag_service, user_service
    ):
        annotation_ids = [annotation.id]

        result = service.present_all_for_user(annotation_ids, user)

        flag_service.all_flagged.assert_called_once_with(user, annotation_ids)
        flag_service.flag_counts.assert_called_once_with(annotation_ids)
        user_service.fetch_all.assert_called_once_with([annotation.userid])

        assert result == [
            # A few indicative fields to show we are serializing
            Any.dict.containing({"id": Any(), "hidden": False})
        ]

    @pytest.mark.parametrize("attribute", ("document", "moderation", "group"))
    @pytest.mark.parametrize("with_preload", (True, False))
    def test_present_all_for_userpreloading_is_effective(
        self,
        service,
        annotation,
        user,
        db_session,
        query_counter,
        attribute,
        with_preload,
    ):
        # Ensure SQLAlchemy forgets all about our annotation
        db_session.flush()
        db_session.expire(annotation)
        if with_preload:
            service.present_all_for_user([annotation.id], user)

        query_counter.reset()
        getattr(annotation, attribute)

        # If we preloaded, we shouldn't execute any queries (and vice versa)
        assert bool(query_counter.count) != with_preload

    @pytest.fixture
    def query_counter(self, db_engine):
        class QueryCounter:
            count = 0

            def __call__(self, *args, **kwargs):
                self.count += 1

            def reset(self):
                self.count = 0

        query_counter = QueryCounter()
        event.listen(db_engine, "before_cursor_execute", query_counter)
        return query_counter

    @pytest.fixture
    def service(self, db_session, links_service, flag_service, user_service):
        return AnnotationJSONService(
            session=db_session,
            links_service=links_service,
            flag_service=flag_service,
            user_service=user_service,
        )

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation(
            moderation=None, groupid="NOT WORLD", tags=["some-tags"]
        )

    @pytest.fixture
    def with_hidden_annotation(self, annotation, factories):
        annotation.moderation = factories.AnnotationModeration()

    @pytest.fixture(autouse=True)
    def Identity(self, patch):
        return patch("h.services.annotation_json.Identity")

    @pytest.fixture(autouse=True)
    def identity_permits(self, patch):
        return patch("h.services.annotation_json.identity_permits")

    @pytest.fixture(autouse=True)
    def DocumentJSONPresenter(self, patch):
        return patch("h.services.annotation_json.DocumentJSONPresenter")


class TestFactory:
    def test_it(
        self,
        pyramid_request,
        AnnotationJSONService,
        flag_service,
        links_service,
        user_service,
    ):
        service = factory(sentinel.context, pyramid_request)

        assert service == AnnotationJSONService.return_value

        AnnotationJSONService.assert_called_once_with(
            session=pyramid_request.db,
            links_service=links_service,
            flag_service=flag_service,
            user_service=user_service,
        )

    @pytest.fixture
    def AnnotationJSONService(self, patch):
        return patch("h.services.annotation_json.AnnotationJSONService")

    @pytest.fixture
    def pyramid_request(self, pyramid_request, factories):
        pyramid_request.user = factories.User()
        return pyramid_request
