Real Time API
=============

.. warning::

   This document describes an API that is in the early stages of being
   documented and refined for public use. Details may change, and your systems
   may break in the future.

In addition to the `HTTP API <http://h.readthedocs.io/en/latest/api/>`_
Hypothesis has a WebSocket-based API that allows developers to receive near
real-time notifications of annotation events.

Overview
--------

To use the Real Time API, you should open a WebSocket connection to the
following endpoint::

    wss://hypothes.is/ws

Communication with this endpoint consists of JSON-encoded messages sent from
client to server and vice versa.

Authorization
-------------

Clients that are only interested in receiving notifications about public
annotations on a page do not need to authenticate. Clients that want to receive
notifications about all updates relevant to a particular user must
authenticate.

Server-side clients can authenticate to the Real Time API by providing an access
token in an Authorization header::

    Authorization: Bearer <token>

Browser-based clients are not able to set this header due to limitations of the
the browser's ``WebSocket`` API. Instead they can authenticate by setting an
``access_token`` query parameter in the URL when connecting::

    var socket = new WebSocket(`wss://hypothes.is/ws?access_token=${token}`)

Server messages
---------------

Each messages from the server will be either an :term:`event` or a
:term:`reply`:

.. glossary::

   event
      An event is sent to clients as a result of an action taken elsewhere in
      the system. For example: if an annotation is made which matches one of the
      client's subscriptions, the client will receive an event message. All
      event messages have a ``type`` field.

   reply
      A reply is sent in response to a message sent by the client. All replies
      have an ``ok`` field which indicates whether the server successfully
      processed the client's message, and a ``reply_to`` field which indicates
      which client message the server is responding to.

Clients should ignore events with types that they do not recognise, as this will
allow us to add new events in future without breaking your client.

.. note::

   We will add documentation for specific event types as we upgrade the
   protocol.

Sending messages
----------------

All messages sent to the server must have a numeric ID which is unique for the
connection. The ID should be sent with the message in the ``id`` field. In
addition, every message sent to the server must have a valid ``type`` field. See
below for the different types of message you can send.

.. contents:: Message types
   :local:
   :depth: 1

``ping``
~~~~~~~~

To verify that the connection is still open, clients can (and are encouraged to)
send a "ping" message:

.. code-block:: json

   {
      "id": 123,
      "type": "ping"
   }

The server replies with a ``pong`` message:

.. code-block:: json

   {
      "ok": true,
      "reply_to": 123,
      "type": "pong"
   }

``whoami``
~~~~~~~~~~

Primarily for debugging purposes, you can send the server a "who am I?" message
to check whether you have authenticated correctly to the WebSocket.

.. code-block:: json

   {
      "id": 123,
      "type": "whoami"
   }

The server will respond with a ``whoyouare`` message:

.. code-block:: json

   {
      "ok": true,
      "reply_to": 123,
      "type": "whoyouare",
      "userid": "acct:joe.bloggs@hypothes.is"
   }
