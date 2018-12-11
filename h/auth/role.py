# -*- coding: utf-8 -*-

#: Administrators. These users have super cow powers.
from __future__ import unicode_literals

Admin = "group:__admin__"

#: Hypothesis staff. These users have limited access to admin functionality.
Staff = "group:__staff__"

#: A request with client-credentials authentication
AuthClient = "group:__authclient__"

#: A request with an authenticated user
#: c.f. ``AuthClient``, which can exist on an authenticated request but
#: there is no user
User = "group:__user__"


#: This role represents an authenticated authclient request that also has a
#: verified forwarded user. This kind of request would also qualify for
#: ``AuthClient`` and ``User`` roles.
AuthClientUser = "group:__authclientuser__"
