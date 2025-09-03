from datetime import datetime
from unittest.mock import sentinel

import pytest
from h_matchers import Any
from pyramid.authorization import Everyone

from h.models import Annotation, AnnotationMetadata, ModerationStatus
from h.security.permissions import Permission
from h.services.annotation_json import AnnotationJSONService, factory
from h.traversal import AnnotationContext


class TestAnnotationJSONService:
    def test_present(
        self,
        service,
        annotation,
        links_service,
        user_service,
        flag_service,
        DocumentJSONPresenter,
    ):
        annotation.created = datetime(2016, 2, 24, 18, 3, 25, 768)  # noqa: DTZ001
        annotation.updated = datetime(2016, 2, 29, 10, 24, 5, 564)  # noqa: DTZ001
        annotation.references = ["pUQBbZOcRA2h_5259SY98Q", "473NFWUVSiqlSDLmpBbNOg"]
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
            "mentions": [],
            "moderation_status": None,
            "hidden": False,
            "flagged": flag_service.flagged.return_value,
            "moderation": {"flagCount": flag_service.flag_count.return_value},
            "actions": ["moderate"],
        }

        DocumentJSONPresenter.assert_called_once_with(annotation.document)
        DocumentJSONPresenter.return_value.asdict.assert_called_once_with()

    def test_present_with_metadata(self, service, annotation):
        data = {
            "lms": {
                "guid": "guid",
                "assignment": {"resource_link_id": "resource_link_id"},
            }
        }
        annotation.slim.meta = AnnotationMetadata(data=data)

        result = service.present(annotation, with_metadata=True)

        assert result["metadata"] == data

    def test_present_without_references(self, service, annotation):
        annotation.references = None

        result = service.present(annotation)

        assert "references" not in result

    def test_present_without_moderation_permission(
        self, service, annotation, identity_permits
    ):
        identity_permits.return_value = False

        result = service.present(annotation)

        assert result["actions"] == []

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

    @pytest.mark.parametrize(
        "group_id,expected_identity_permits_calls",
        [
            ("__world__", 1),
            ("foo", 2),
        ],
    )
    def test_present_skips_the_read_permission_check_if_group_is_world(
        self,
        service,
        annotation,
        identity_permits,
        group_id,
        expected_identity_permits_calls,
    ):
        annotation.shared = True
        annotation.groupid = group_id

        presented = service.present(annotation)

        assert identity_permits.call_count == expected_identity_permits_calls
        assert presented["permissions"]["read"] == ["group:__world__"]

    @pytest.mark.parametrize("shared", [True, False])
    @pytest.mark.parametrize(
        "moderation_status", [None, ModerationStatus.APPROVED, ModerationStatus.DENIED]
    )
    def test_present_moderation_status(
        self, service, annotation, shared, moderation_status
    ):
        annotation.shared = shared
        annotation.moderation_status = moderation_status

        result = service.present(annotation)

        if not shared and not moderation_status:
            assert result["moderation_status"] is None

        elif not moderation_status:
            assert result["moderation_status"] == "APPROVED"

        elif moderation_status and shared:
            assert result["moderation_status"] == moderation_status.value

    def test_present_only_shows_moderation_to_moderators(
        self, service, annotation, user, identity_permits, Identity, matchers
    ):
        identity_permits.return_value = False

        result = service.present(annotation, user)

        Identity.from_models.assert_called_once_with(user=user)
        identity_permits.assert_called_once_with(
            identity=Identity.from_models.return_value,
            context=matchers.InstanceOf(AnnotationContext, annotation=annotation),
            permission=Permission.Annotation.MODERATE,
        )

        assert "moderation" not in result

    @pytest.mark.usefixtures("with_hidden_annotation")
    def test_present_hidden_status_is_not_shown_to_creator(
        self, service, annotation, user
    ):
        annotation.userid = user.userid

        result = service.present(annotation, user)

        assert not result["hidden"]

    @pytest.mark.usefixtures("with_hidden_annotation")
    def test_present_hidden_censors_content_for_normal_users(
        self, service, annotation, user, identity_permits
    ):
        identity_permits.return_value = False

        result = service.present(annotation, user)

        assert result["hidden"]
        assert not result["text"]
        assert not result["tags"]

    @pytest.mark.usefixtures("with_hidden_annotation")
    def test_present_hidden_shows_everything_to_moderators(
        self, service, annotation, user, identity_permits
    ):
        identity_permits.return_value = True

        result = service.present(annotation, user)

        assert result["hidden"]
        assert result["text"]
        assert result["tags"]

    def test_present_all_for_user(
        self,
        service,
        annotation,
        user,
        annotation_read_service,
        flag_service,
        user_service,
    ):
        annotation_read_service.get_annotations_by_id.return_value = [annotation]

        result = service.present_all_for_user(sentinel.annotation_ids, user)

        annotation_read_service.get_annotations_by_id.assert_called_once_with(
            ids=sentinel.annotation_ids,
            eager_load=[
                Annotation.document,
                Annotation.group,
                Annotation.mentions,
            ],
        )
        flag_service.all_flagged.assert_called_once_with(user, sentinel.annotation_ids)
        flag_service.flag_counts.assert_called_once_with(sentinel.annotation_ids)
        user_service.fetch_all.assert_called_once_with([annotation.userid])

        assert result == [
            # A few indicative fields to show we are serializing
            Any.dict.containing({"id": Any(), "hidden": False})
        ]

    @pytest.fixture
    def service(
        self,
        annotation_read_service,
        links_service,
        flag_service,
        user_service,
        mention_service,
        pyramid_request,
    ):
        return AnnotationJSONService(
            annotation_read_service=annotation_read_service,
            links_service=links_service,
            flag_service=flag_service,
            user_service=user_service,
            mention_service=mention_service,
            request=pyramid_request,
        )

    @pytest.fixture
    def user(self, factories):
        return factories.User()

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation(
            groupid="NOT WORLD",
            tags=["some-tags"],
            slim=factories.AnnotationSlim(),
        )

    @pytest.fixture
    def with_hidden_annotation(self, annotation):
        annotation.moderation_status = ModerationStatus.DENIED

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
        annotation_read_service,
        flag_service,
        links_service,
        user_service,
        mention_service,
    ):
        service = factory(sentinel.context, pyramid_request)

        AnnotationJSONService.assert_called_once_with(
            annotation_read_service=annotation_read_service,
            links_service=links_service,
            flag_service=flag_service,
            user_service=user_service,
            mention_service=mention_service,
            request=pyramid_request,
        )
        assert service == AnnotationJSONService.return_value

    @pytest.fixture
    def AnnotationJSONService(self, patch):
        return patch("h.services.annotation_json.AnnotationJSONService")
