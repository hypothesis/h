import json

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from ..models import Annotation
from .reply_template import generate_notifications


def run(request):
    """
    Subscribe to the ``annotations`` topic and send notifications for events as
    necessary.

    It is safe to run several of these worker functions as they all read from
    the same channel. NSQ will distribute messages among available workers in a
    round-robin fashion.
    """
    for message in request.get_queue_reader('annotations', 'notification'):
        data = json.loads(message.body)
        action = data['action']
        annotation = Annotation(**data['annotation'])
        mailer = get_mailer(request)
        notifications = generate_notifications(request, annotation, action)
        for (subject, body, html, recipients) in notifications:
            m = Message(subject=subject, recipients=recipients,
                        body=body, html=html)
            mailer.send_immediately(m)
        message.fin()
