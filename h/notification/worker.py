# -*- coding: utf-8 -*-
import json

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from h.api import storage
from h.notification.reply_template import generate_notifications


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
        with request.tm:
            send_notifications(message)

    def send_notifications(message):
        data = json.loads(message.body)
        action = data['action']
        annotation = storage.annotation_from_dict(data['annotation'])
        mailer = get_mailer(request)
        notifications = generate_notifications(request, annotation, action)
        for (subject, body, html, recipients) in notifications:
            m = Message(subject=subject, recipients=recipients,
                        body=body, html=html)
            mailer.send_immediately(m)

    reader = request.get_queue_reader('annotations', 'notification')
    reader.on_message.connect(handle_message)
    reader.start(block=True)
