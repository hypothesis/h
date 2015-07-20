import json

from h.api.nipsa import models


def _publish(request, data):
    request.get_queue_writer().publish("nipsa_user_requests", data)


def index():
    """Return a list of all the NIPSA'd user IDs.

    :rtype: list of unicode strings

    """
    return [nipsa_user.userid for nipsa_user in models.NipsaUser.all()]


def nipsa(request, userid):
    """NIPSA a user.

    Add the given user's ID to the list of NIPSA'd user IDs.
    If the user is already NIPSA'd then nothing will happen (but a "nipsa"
    message for the user will still be published to the queue).

    """
    nipsa_user = models.NipsaUser.get_by_id(userid)
    if not nipsa_user:
        nipsa_user = models.NipsaUser(userid)
        request.db.add(nipsa_user)

    _publish(request, json.dumps({"action": "nipsa", "userid": userid}))


def unnipsa(request, userid):
    """Un-NIPSA a user.

    If the user isn't NIPSA'd then nothing will happen (but an "unnipsa"
    message for the user will still be published to the queue).

    """
    nipsa_user = models.NipsaUser.get_by_id(userid)
    if nipsa_user:
        request.db.delete(nipsa_user)

    _publish(request, json.dumps({"action": "unnipsa", "userid": userid}))


def is_nipsad(userid):
    """Return True if the given user is on the NIPSA list, False if not."""
    return (models.NipsaUser.get_by_id(userid) is not None)
