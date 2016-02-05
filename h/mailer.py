# -*- coding: utf-8 -*-
"""A module for sending emails asynchronously.

Most code that sends emails should do so through this module.

User code should call the send() function to cause an email to be sent
asynchronously.

"""
import json

import pyramid_mailer
import pyramid_mailer.message


def send(request, recipients, subject, body):
    """Cause an email to be sent asynchronously.

    :param request: the request object for the request that wants to send the
        email
    :type request: pyramid.request.Request

    :param recipients: the list of email addresses to send the email to
    :type recipients: list of unicode strings

    :param subject: the subject of the email
    :type subject: unicode

    :param body: the body of the email
    :type body: unicode

    """
    request.get_queue_writer().publish(
        "email", {"recipients": recipients, "subject": subject, "body": body})


def worker(request):
    """A hypothesis-worker function for sending emails.

    Connects to the "email" topic that send() above publishes to and
    sends an email for each message received.

    """
    def handle_message(_, message):
        """Receive a message from nsq and send it as an email."""
        body = json.loads(message.body)
        email = pyramid_mailer.message.Message(
            subject=body["subject"], recipients=body["recipients"],
            body=body["body"])
        pyramid_mailer.get_mailer(request).send_immediately(email)

    reader = request.get_queue_reader("email", "mailer")
    reader.on_message.connect(handle_message)
    reader.start(block=True)
