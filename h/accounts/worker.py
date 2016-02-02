# -*- coding: utf-8 -*-
import json

import pyramid_mailer


def worker(request):
    """Subscribe to the "activations" topic and send activation emails."""
    def handle_message(reader, message):
        body = json.loads(message.body)
        email = pyramid_mailer.message.Message(
            subject=body['subject'], recipients=body['recipients'],
            body=body['body'])
        pyramid_mailer.get_mailer(request).send_immediately(email)

    reader = request.get_queue_reader('activations', 'mailer')
    reader.on_message.connect(handle_message)
    reader.start(block=True)
