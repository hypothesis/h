import json

import transaction

from ..models import Annotation
from .reply_template import send_notifications


def run(request):
    """
    Subscribe to the ``annotations`` topic and send notifications for events as
    necessary.

    It is safe to run several of these worker functions as they all read from
    the same channel. NSQ will distribute messages among available workers in a
    round-robin fashion.
    """
    def handle_message(reader, message=None):
        if message is None:
            return
        data = json.loads(message.body)
        action = data['action']
        annotation = Annotation(**data['annotation'])
        send_notifications(request, annotation, action)
        transaction.commit()

    reader = request.get_queue_reader('annotations', 'notification')
    reader.on_message.connect(handle_message)
    reader.start(block=True)
