import logging
import os
from dataclasses import dataclass

from celery import Celery

from h.events import AnnotationEvent
from h.services.annotation_read import AnnotationReadService

logger = logging.getLogger(__name__)


@dataclass
class AuthorityQueueConfiguration:
    broker_url: str
    task_name: str


class AnnotationAuthorityQueueService:
    def __init__(
        self, annotation_read_service: AnnotationReadService, annotation_json_service
    ):
        self._annotation_read_service = annotation_read_service
        self._annotation_json_service = annotation_json_service

    def publish(self, event: AnnotationEvent):
        annotation = self._annotation_read_service.get_annotation_by_id(
            event.annotation_id,
        )
        authority_queue_config = self._read_authority_queue_config(annotation.authority)
        if not authority_queue_config:
            return

        if event.action != "create":
            return

        if not annotation.mentions:
            return

        annotation_dict = self._annotation_json_service.present_for_user(
            annotation=annotation, user=annotation.slim.user, with_metadata=True
        )

        payload = {
            "action": event.action,
            "annotation": annotation_dict,
        }

        authority_celery = Celery(annotation.authority)
        authority_celery.conf.broker_url = authority_queue_config.broker_url

        authority_celery.send_task(
            authority_queue_config.task_name, kwargs={"event": payload}
        )

    def _read_authority_queue_config(
        self, authority: str
    ) -> AuthorityQueueConfiguration | None:
        broker_url = os.environ.get(
            f"ANNOTATION_AUTHORITY_QUEUE_BROKER_URL_{authority.upper()}"
        )
        task_name = os.environ.get(
            f"ANNOTATION_AUTHORITY_QUEUE_TASK_NAME_{authority.upper()}"
        )
        if broker_url is None or task_name is None:
            return None

        return AuthorityQueueConfiguration(broker_url=broker_url, task_name=task_name)


def factory(_context, request) -> AnnotationAuthorityQueueService:
    return AnnotationAuthorityQueueService(
        annotation_read_service=request.find_service(AnnotationReadService),
        annotation_json_service=request.find_service(name="annotation_json"),
    )
