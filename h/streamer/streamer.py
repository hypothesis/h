import logging
import sys

import gevent

from h import db
from h.streamer import messages, websocket

log = logging.getLogger(__name__)

# Queue of messages to process, from both client websockets and message queues
# to which the streamer is subscribed.
#
# The maxsize ensures that memory used by this queue is bounded. Producers
# writing to the queue must consider their behaviour when the queue is full,
# using .put(...) with a timeout or .put_nowait(...) as appropriate.
WORK_QUEUE = gevent.queue.Queue(maxsize=4096)

# Message queues that the streamer processes messages from
ANNOTATION_TOPIC = "annotation"
USER_TOPIC = "user"

TOPIC_HANDLERS = {
    ANNOTATION_TOPIC: messages.handle_annotation_event,
    USER_TOPIC: messages.handle_user_event,
}


class UnknownMessageType(Exception):
    """Raised if a message in the work queue if of an unknown type."""


def start(event):
    """
    Start some greenlets to process the incoming data from the message queue.

    This subscriber is called when the application is booted, and kicks off
    greenlets running `process_queue` for each message queue we subscribe to.
    The function does not block.
    """
    settings = event.app.registry.settings

    greenlets = [
        # Start greenlets to process messages from RabbitMQ
        gevent.spawn(messages.process_messages, settings, ANNOTATION_TOPIC, WORK_QUEUE),
        gevent.spawn(messages.process_messages, settings, USER_TOPIC, WORK_QUEUE),
        # And one to process the queued work
        gevent.spawn(process_work_queue, settings, WORK_QUEUE),
    ]

    # Start a "greenlet of last resort" to monitor the worker greenlets and
    # bail if any unexpected errors occur.
    gevent.spawn(supervise, greenlets)


def process_work_queue(settings, queue):
    """
    Process each message from the queue in turn, handling exceptions.

    This is the core of the streamer: we pull messages off the work queue,
    dispatching them as appropriate. The handling of each message is wrapped in
    code that ensures the database session is appropriately committed and
    closed between messages.
    """

    session = db.Session(bind=db.make_engine(settings))

    for msg in queue:
        try:
            # All access to the database in the streamer is currently
            # read-only, so enforce that:
            session.execute(
                "SET TRANSACTION ISOLATION LEVEL "
                "SERIALIZABLE "
                "READ ONLY "
                "DEFERRABLE"
            )

            if isinstance(msg, messages.Message):
                messages.handle_message(msg, settings, session, TOPIC_HANDLERS)
            elif isinstance(msg, websocket.Message):
                websocket.handle_message(msg, session)
            else:
                raise UnknownMessageType(repr(msg))

        except (KeyboardInterrupt, SystemExit):
            session.rollback()
            raise
        except Exception as exc:
            log.warning("Caught exception handling streamer message:", exc_info=exc)
            session.rollback()
        else:
            session.commit()
        finally:
            session.close()


def supervise(greenlets):
    try:
        gevent.joinall(greenlets, raise_error=True)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:  # noqa: E722
        log.critical("Unexpected exception in streamer greenlet:", exc_info=True)
    else:
        log.critical("Unexpected early exit of streamer greenlets. Aborting!")
    # If the worker greenlets exit early, our best option is to kill the worker
    # process and let the app server take care of restarting it.
    sys.exit(1)
