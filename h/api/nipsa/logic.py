import json

from h.api.nipsa import models


def _publish(request, data):
    request.get_queue_writer().publish("nipsa_user_requests", data)


def index():
    """Return a list of all the NIPSA'd user IDs.

    :rtype: list of unicode strings

    """
    return [nipsa_user.user_id for nipsa_user in models.NipsaUser.all()]


def nipsa(request, user_id):
    """NIPSA a user.

    Add the given user's ID to the list of NIPSA'd user IDs.
    If the user is already NIPSA'd then nothing will happen (but a "nipsa"
    message for the user will still be published to the queue).

    """
    nipsa_user = models.NipsaUser.get_by_id(user_id)
    if not nipsa_user:
        nipsa_user = models.NipsaUser(user_id)
        request.db.add(nipsa_user)

    _publish(request, json.dumps({"action": "nipsa", "user_id": user_id}))


def unnipsa(request, user_id):
    """Un-NIPSA a user.

    If the user isn't NIPSA'd then nothing will happen (but an "unnipsa"
    message for the user will still be published to the queue).

    """
    nipsa_user = models.NipsaUser.get_by_id(user_id)
    if nipsa_user:
        request.db.delete(nipsa_user)

    _publish(request, json.dumps({"action": "unnipsa", "user_id": user_id}))


def is_nipsad(user_id):
    """Return True if the given user is on the NIPSA list, False if not."""
    return (models.NipsaUser.get_by_id(user_id) is not None)
