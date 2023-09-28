from h.search.client import get_client
from h.search.config import init
from h.search.core import Search
from h.search.query import (
    AuthorityFilter,
    DeletedFilter,
    Limiter,
    TagsAggregation,
    TopLevelAnnotationsFilter,
    UserFilter,
    UsersAggregation,
)

__all__ = (
    "Search",
    "TopLevelAnnotationsFilter",
    "DeletedFilter",
    "Limiter",
    "UserFilter",
    "AuthorityFilter",
    "TagsAggregation",
    "UsersAggregation",
    "get_client",
    "init",
)


def includeme(config):  # pragma: no cover
    settings = config.registry.settings

    kwargs = {}
    kwargs["max_retries"] = settings.get("es.client.max_retries", 3)
    kwargs["retry_on_timeout"] = settings.get("es.client.retry_on_timeout", False)
    kwargs["timeout"] = settings.get("es.client.timeout", 10)

    if "es.client_poolsize" in settings:
        kwargs["maxsize"] = settings["es.client_poolsize"]

    settings.setdefault("es.index", "hypothesis")

    # Add a property to all requests for easy access to the elasticsearch 6.x
    # client. This can be used for direct or bulk access without having to
    # reread the settings.
    config.registry["es.client"] = get_client(settings)
    config.add_request_method(lambda r: r.registry["es.client"], name="es", reify=True)
