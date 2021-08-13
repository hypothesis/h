class Role:
    # Administrators. These users have super cow powers.
    ADMIN = "role:admin"

    # Hypothesis staff. These users have limited access to admin functionality.
    STAFF = "role:staff"

    # A request with auth client credentials authentication
    AUTH_CLIENT = "role:auth_client"

    # A request with an authenticated user
    USER = "role:user"

    # This role represents an authenticated auth client request that also has
    # a verified forwarded user. This kind of request would also qualify for
    # `AUTH_CLIENT` and `USER` roles.
    AUTH_CLIENT_FORWARDED_USER = "role:auth_client_forwarded_user"
    # NOTE: I'm pretty sure this doesn't grant anything and can be removed. If
    # you want the permissions for `AUTH_CLIENT` and `USER` roles you just
    # grant them both.
