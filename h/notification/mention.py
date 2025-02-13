import logging
from dataclasses import dataclass

from h.models import Annotation, Document, User

logger = logging.getLogger(__name__)


@dataclass
class MentionNotification:
    """A data structure representing a mention notification in an annotation."""

    mentioning_user: User
    mentioned_user: User
    annotation: Annotation
    document: Document
