# -*- coding: utf-8 -*-

from __future__ import unicode_literals


class UserJSONPresenter(object):
    """Present a user.

    Format a user's data in JSON for use in API services. Only include
    properties that are public-facing.
    """

    def __init__(self, user):
        self.user = user

    def asdict(self):
        return {
            "authority": self.user.authority,
            "userid": self.user.userid,
            "username": self.user.username,
            "display_name": self.user.display_name,
        }


class TrustedUserJSONPresenter(object):
    """Present a user to a trusted consumer.

    Format a user's data in JSON for use in API services, including any
    sensitive/private properties.
    """

    def __init__(self, user):
        self.user = user

    def asdict(self):
        user_presented = UserJSONPresenter(self.user).asdict()
        user_presented["email"] = self.user.email
        return user_presented
