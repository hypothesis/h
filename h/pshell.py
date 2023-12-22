import os
from contextlib import suppress

import sqlalchemy
from transaction.interfaces import NoTransaction

from h import models, services, tasks


def setup(env):
    from tests.common import factories  # pylint:disable=import-outside-toplevel

    request = env["request"]

    # Make Pyramid things like route_url() and static_url() use the right
    # hostname and port when called from pshell.
    request.environ["HTTP_HOST"] = os.environ["HTTP_HOST"]

    request.tm.begin()

    env["tm"] = request.tm
    env["tm"].__doc__ = "Active transaction manager (a transaction is already begun)."

    env["db"] = env["session"] = request.db
    env["db"].__doc__ = "Active DB session."

    env["m"] = env["models"] = models
    env["m"].__doc__ = "The h.models package."

    env["f"] = env["factories"] = factories
    env["f"].__doc__ = "The test factories for quickly creating objects."
    factories.set_session(request.db)

    env["t"] = env["tasks"] = tasks
    env["tasks"].__doc__ = "The h.tasks package."

    env["s"] = env["services"] = services
    env["s"].__doc__ = "The h.services package."

    env["select"] = sqlalchemy.select
    env["select"].__doc__ = "The sqlalchemy.select function."

    try:
        yield
    finally:
        with suppress(NoTransaction):
            request.tm.abort()
