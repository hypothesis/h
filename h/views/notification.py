from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config

from h.models import Subscriptions


@view_config(route_name="unsubscribe", renderer="h:templates/unsubscribe.html.jinja2")
def unsubscribe(request):
    token = request.matchdict["token"]
    try:
        payload = request.registry.notification_serializer.loads(token)
    except ValueError as err:
        raise HTTPNotFound() from err

    subscriptions = request.db.query(Subscriptions).filter_by(
        type=payload["type"], uri=payload["uri"]
    )

    for subscription in subscriptions:
        if subscription.active:
            subscription.active = False

    return {}
