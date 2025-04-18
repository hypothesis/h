import json
import logging
from dataclasses import dataclass

from celery import Celery
from kombu import Connection

from h.services.annotation_read import AnnotationReadService

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthorityQueueConfiguration:
    """Celery setting for an authority specific queue."""

    broker_url: str
    queue_name: str
    task_name: str


class AnnotationAuthorityQueueService:
    """A service to publish annotation events to authority specific queues."""

    def __init__(
        self,
        authority_queue_config_json: str | None,
        annotation_read_service: AnnotationReadService,
        annotation_json_service,
    ):
        self._authority_queue_config = self._parse_authority_queue_config(
            authority_queue_config_json
        )
        self._annotation_read_service = annotation_read_service
        self._annotation_json_service = annotation_json_service

    def publish(self, event_action: str, annotation_id: str) -> None:
        annotation = self._annotation_read_service.get_annotation_by_id(annotation_id)
        if not annotation:
            LOG.error("Annotation %r not found", annotation_id)
            return

        authority_queue_config = self._authority_queue_config.get(annotation.authority)
        if not authority_queue_config:
            return

        if event_action not in {"create", "update"} or not annotation.mentions:
            # For now we'll limit the events to only those that create annotations that contain mentions
            LOG.info(
                "Skipping event '%s' for annotation '%s'", event_action, annotation.id
            )
            return

        annotation_dict = self._annotation_json_service.present_for_user(
            annotation=annotation, user=annotation.slim.user, with_metadata=True
        )
        # We already done the work to sanitize the text, send that value to the queue
        annotation_dict["text_rendered"] = annotation.text_rendered
        # Also expose the quoted text if it exists
        annotation_dict["quote"] = annotation.quote

        payload = {
            "action": event_action,
            "annotation": annotation_dict,
        }

        authority_celery = Celery(annotation.authority)
        with Connection(authority_queue_config.broker_url) as connection:
            authority_celery.send_task(
                authority_queue_config.task_name,
                queue=authority_queue_config.queue_name,
                # We need to pass the connection explicitly to avoid using the default connection / broker
                connection=connection,
                # Expire these tasks just in case something prevents them from being processed
                expires=60 * 60 * 24,
                kwargs={"event": payload},
            )
            LOG.info(
                "Published event %s for annotation %s to %s",
                event_action,
                annotation.id,
                annotation.authority,
            )

    def _parse_authority_queue_config(
        self, config_json: str | None
    ) -> dict[str, AuthorityQueueConfiguration]:
        """Parse the authority queue config JSON string into dictionary by authority name."""
        if not config_json:
            LOG.info("No authority queue config found")
            return {}
        try:
            config = json.loads(config_json)
        except json.JSONDecodeError:
            LOG.exception("Failed to parse authority queue config: %s", config_json)
            return {}

        parsed_config = {}
        for authority, authority_queue_config in config.items():
            broker_url = authority_queue_config.get("broker_url")
            queue_name = authority_queue_config.get("queue_name")
            task_name = authority_queue_config.get("task_name")

            if not all([broker_url, queue_name, task_name]):
                LOG.error(
                    "Invalid authority queue config for %s: %s",
                    authority,
                    authority_queue_config,
                )
                continue

            parsed_config[authority] = AuthorityQueueConfiguration(
                broker_url=broker_url, queue_name=queue_name, task_name=task_name
            )

        return parsed_config


def factory(_context, request) -> AnnotationAuthorityQueueService:
    return AnnotationAuthorityQueueService(
        authority_queue_config_json=request.registry.settings.get(
            "h.authority_queue_config"
        ),
        annotation_read_service=request.find_service(AnnotationReadService),
        annotation_json_service=request.find_service(name="annotation_json"),
    )
