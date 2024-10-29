from unittest.mock import sentinel

import pytest
from h_matchers import Any

from h.models import GroupMembership
from h.services.bulk_api.annotation import (
    BulkAnnotation,
    BulkAnnotationService,
    service_factory,
)


class TestBulkAnnotationService:
    AUTHORITY = "my.authority"

    @pytest.mark.parametrize(
        "key,value,visible",
        (
            (None, None, True),
            ("shared", False, False),
            ("deleted", True, False),
            ("nipsad", True, False),
            ("with_metadata", True, True),
            ("with_metadata", False, True),
            ("moderated", True, False),
            ("created", "2020-01-01", False),
            ("created", "2020-01-02", True),
            ("created", "2022-01-01", True),
            ("created", "2022-01-02", False),
        ),
    )
    @pytest.mark.parametrize("username", ["USERNAME", "username", "user.name"])
    def test_it_with_single_annotation(
        self, svc, factories, key, value, visible, username
    ):
        values = {
            "shared": True,
            "deleted": False,
            "nipsad": False,
            "moderated": False,
            "created": "2021-01-01",
            "with_metadata": True,
        }
        if key:
            values[key] = value

        viewer = factories.User(authority=self.AUTHORITY)
        author = factories.User(
            authority=self.AUTHORITY, nipsa=values["nipsad"], username=username
        )
        group = factories.Group(
            memberships=[GroupMembership(user=author), GroupMembership(user=viewer)]
        )
        anno_slim = factories.AnnotationSlim(
            user=author,
            group=group,
            shared=values["shared"],
            deleted=values["deleted"],
            created=values["created"],
            moderated=values["moderated"],
        )

        if values["with_metadata"]:
            factories.AnnotationMetadata(
                annotation_slim=anno_slim, data={"some": "value"}
            )

        annotations = svc.annotation_search(
            authority=self.AUTHORITY,
            username="USERNAME",
            created={"gt": "2020-01-01", "lte": "2022-01-01"},
        )

        if visible:
            assert annotations == [
                BulkAnnotation(
                    username=author.username,
                    authority_provided_id=group.authority_provided_id,
                    metadata={"some": "value"} if values["with_metadata"] else {},
                )
            ]
        else:
            assert not annotations

    def test_it_with_more_complex_grouping(self, svc, factories):
        viewer, author = factories.User.create_batch(2, authority=self.AUTHORITY)

        annotations = [
            factories.AnnotationSlim(
                user=author,
                group=factories.Group(
                    memberships=[GroupMembership(user=user) for user in group_members]
                ),
                shared=True,
                deleted=False,
            )
            for group_members in (
                # The first two annotations should match, because they are in
                # groups the viewer is in
                [author, viewer],
                [author, viewer],
                # This one is just noise and shouldn't match
                [author],
            )
        ]

        matched_annos = svc.annotation_search(
            authority=self.AUTHORITY,
            username=viewer.username,
            created={"gt": "2020-01-01", "lte": "2099-01-01"},
        )

        # Only the first two annotations should match
        assert (
            matched_annos
            == Any.list.containing(
                [
                    BulkAnnotation(
                        username=author.username,
                        authority_provided_id=annotation.group.authority_provided_id,
                        metadata={},
                    )
                    for annotation in annotations[:2]
                ]
            ).only()
        )

    @pytest.fixture
    def svc(self, db_session):
        return BulkAnnotationService(db_session)


class TestServiceFactory:
    def test_it(self, pyramid_request, BulkAnnotationService):
        svc = service_factory(sentinel.context, pyramid_request)

        BulkAnnotationService.assert_called_once_with(db_session=pyramid_request.db)
        assert svc == BulkAnnotationService.return_value

    @pytest.fixture
    def BulkAnnotationService(self, patch):
        return patch("h.services.bulk_api.annotation.BulkAnnotationService")
