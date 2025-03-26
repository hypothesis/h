import json
from unittest.mock import sentinel

import pytest

from h.services.annotation_authority_queue import (
    AnnotationAuthorityQueueService,
    AuthorityQueueConfiguration,
    factory,
)


class TestAnnotationAuthorityQueueService:
    def test_publish_when_no_authority_queue_config(self, svc, Celery):
        svc._authority_queue_config = {}  # noqa: SLF001

        svc.publish("create", sentinel.annotation_id)

        Celery.assert_not_called()

    def test_publish_when_no_creation_or_edit(
        self, svc, Celery, annotation_read_service, annotation
    ):
        annotation_read_service.get_annotation_by_id.return_value = annotation

        svc.publish("delete", sentinel.annotation_id)

        Celery.assert_not_called()

    def test_publish_with_no_mentions(self, svc, Celery, annotation_read_service):
        svc.publish("create", sentinel.annotation_id)

        annotation_read_service.get_annotation_by_id.assert_called_once_with(
            sentinel.annotation_id
        )
        Celery.assert_not_called()

    def test_publish(
        self,
        svc,
        Celery,
        annotation_read_service,
        annotation_json_service,
        annotation,
        Connection,
    ):
        annotation_presented = {"id": annotation.id}
        annotation_json_service.present_for_user.return_value = annotation_presented
        annotation_read_service.get_annotation_by_id.return_value = annotation

        svc.publish("create", sentinel.annotation_id)

        annotation_read_service.get_annotation_by_id.assert_called_once_with(
            sentinel.annotation_id
        )
        annotation_json_service.present_for_user.assert_called_once_with(
            annotation=annotation_read_service.get_annotation_by_id.return_value,
            user=annotation_read_service.get_annotation_by_id.return_value.slim.user,
            with_metadata=True,
        )
        assert annotation_presented["text_rendered"] == annotation.text_rendered
        assert annotation_presented["quote"] == annotation.quote
        Celery.assert_called_once_with(
            annotation_read_service.get_annotation_by_id.return_value.authority,
        )
        Connection.assert_called_once_with("url")
        Celery.return_value.send_task.assert_called_once_with(
            "task",
            queue="queue",
            connection=Connection.return_value.__enter__.return_value,
            expires=60 * 60 * 24,
            kwargs={
                "event": {
                    "action": "create",
                    "annotation": annotation_presented,
                }
            },
        )

    def test_publish_with_invalid_annotation(
        self, svc, Celery, annotation_read_service
    ):
        annotation_read_service.get_annotation_by_id.return_value = None

        svc.publish("create", sentinel.annotation_id)

        annotation_read_service.get_annotation_by_id.assert_called_once_with(
            sentinel.annotation_id
        )
        Celery.assert_not_called()

    def test_parse_config_when_not_present(self, svc):
        assert not svc._parse_authority_queue_config(None)  # noqa: SLF001

    def test_parse_config_when_invalid_json(self, svc):
        assert not svc._parse_authority_queue_config("{")  # noqa: SLF001

    def test_parse_config_when_missing_key(self, svc):
        assert not svc._parse_authority_queue_config(  # noqa: SLF001
            json.dumps({"lms": {"broker_url": "url"}})
        )

    def test_parse_config_with_config(self, svc, valid_config):
        config = svc._parse_authority_queue_config(valid_config)  # noqa: SLF001

        assert config["lms"] == AuthorityQueueConfiguration(
            broker_url="url", queue_name="queue", task_name="task"
        )

    @pytest.fixture
    def Celery(self, patch):
        return patch("h.services.annotation_authority_queue.Celery")

    @pytest.fixture
    def Connection(self, patch):
        return patch("h.services.annotation_authority_queue.Connection")

    @pytest.fixture
    def valid_config(self):
        return json.dumps(
            {
                "lms": {
                    "broker_url": "url",
                    "queue_name": "queue",
                    "task_name": "task",
                }
            }
        )

    @pytest.fixture
    def annotation(self, factories):
        user = factories.User(authority="lms")
        return factories.Annotation(
            slim=factories.AnnotationSlim(user=user),
            userid=user.userid,
            mentions=[factories.Mention()],
        )

    @pytest.fixture
    def svc(self, annotation_read_service, annotation_json_service, valid_config):
        return AnnotationAuthorityQueueService(
            authority_queue_config_json=valid_config,
            annotation_read_service=annotation_read_service,
            annotation_json_service=annotation_json_service,
        )


class TestFactory:
    def test_it(
        self,
        pyramid_request,
        annotation_read_service,
        AnnotationAuthorityQueueService,
        annotation_json_service,
    ):
        service = factory(sentinel.context, pyramid_request)

        AnnotationAuthorityQueueService.assert_called_once_with(
            authority_queue_config_json=pyramid_request.registry.settings.get(
                "h.authority_queue_config"
            ),
            annotation_read_service=annotation_read_service,
            annotation_json_service=annotation_json_service,
        )

        assert service == AnnotationAuthorityQueueService.return_value

    @pytest.fixture
    def AnnotationAuthorityQueueService(self, patch):
        return patch(
            "h.services.annotation_authority_queue.AnnotationAuthorityQueueService"
        )
