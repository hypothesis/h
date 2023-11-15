from datetime import datetime, timedelta
from unittest.mock import call

import pytest

from h.tasks.annotations import fill_annotation_slim


class TestFillPKAndUserId:
    AUTHORITY_1 = "AUTHORITY_1"
    AUTHORITY_2 = "AUTHORITY_2"

    USERNAME_1 = "USERNAME_1"
    USERNAME_2 = "USERNAME_2"

    def test_it(self, factories, annotation_write_service):
        now = datetime.now()
        annos = factories.Annotation.create_batch(10, created=now)
        factories.Annotation.create_batch(10, deleted=True)
        factories.Annotation.create_batch(10, created=now + timedelta(days=10))

        fill_annotation_slim(
            batch_size=10, since=now - timedelta(days=1), until=now + timedelta(days=1)
        )

        annotation_write_service.upsert_annotation_slim.assert_has_calls(
            [call(anno) for anno in annos], any_order=True
        )

    @pytest.fixture(autouse=True)
    def celery(self, patch, pyramid_request):
        cel = patch("h.tasks.annotations.celery", autospec=False)
        cel.request = pyramid_request
        return cel
