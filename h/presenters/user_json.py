# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class UserJSONPresenter(object):
    """
    Present a user in the JSON format returned by API requests.

    Note that this presenter as of now returns some information
    that should not be publicly available, like the users email
    address. This is fine for now because it is only used in
    places where the caller has access to this. We would need
    to refactor this as soon as we use this presenter for a
    public API.
    """

    def __init__(self, user):
        self.user = user

    def asdict(self):
        return {
            "authority": self.user.authority,
            "email": self.user.email,
            "userid": self.user.userid,
            "username": self.user.username,
            "display_name": self.user.display_name,
        }
