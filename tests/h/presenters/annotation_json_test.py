import datetime

import pytest
from pyramid.authorization import Everyone

from h.presenters.annotation_json import AnnotationJSONPresenter


class TestAnnotationJSONPresenter:
    def test_asdict(
        self, present, annotation, links_service, user_service, DocumentJSONPresenter
    ):
        annotation.created = datetime.datetime(2016, 2, 24, 18, 3, 25, 768)
        annotation.updated = datetime.datetime(2016, 2, 29, 10, 24, 5, 564)
        annotation.references = ["referenced-id-1", "referenced-id-2"]
        annotation.extra = {"extra-1": "foo", "extra-2": "bar"}

        result = present()

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

    def test_asdict_without_references(self, present, annotation):
        annotation.references = None

        result = present()

        assert "references" not in result

    def test_asdict_extra_inherits_correctly(self, present, annotation):
        annotation.extra = {"id": "DIFFERENT"}

        presented = present()

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
    def test_read_permission(
        self,
        present,
        annotation,
        identity_permits,
        shared,
        readable_by,
        permission_template,
    ):
        annotation.shared = shared
        identity_permits.return_value = readable_by

        presented = present()

        permission = permission_template.format(annotation=annotation)
        assert presented["permissions"]["read"] == [permission]

    def test_we_skip_the_read_permission_check_if_group_is_world(
        self, present, annotation, identity_permits
    ):
        annotation.shared = True
        annotation.groupid = "__world__"

        presented = present()

        identity_permits.assert_not_called()
        assert presented["permissions"]["read"] == ["group:__world__"]

    @pytest.fixture
    def present(self, annotation, links_service, user_service):
        presenter = AnnotationJSONPresenter(
            links_service=links_service, user_service=user_service
        )

        def present():
            return presenter.present(annotation)

        return present

    @pytest.fixture
    def annotation(self, factories):
        return factories.Annotation(groupid="NOT WORLD")

    @pytest.fixture(autouse=True)
    def DocumentJSONPresenter(self, patch):
        return patch("h.presenters.annotation_json.DocumentJSONPresenter")

    @pytest.fixture(autouse=True)
    def identity_permits(self, patch):
        return patch("h.presenters.annotation_json.identity_permits")
