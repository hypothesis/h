from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config

from h.services import SubscriptionService
from h.services.subscription import InvalidUnsubscribeToken


@view_config(route_name="unsubscribe", renderer="h:templates/unsubscribe.html.jinja2")
def unsubscribe(request):
    """
    Unsubscribe a user from a particular type of notification.

    This is powered by a token which is produced by the SubscriptionService
    which encodes a user and subscription type.

    This URL is visited from emails produced in, for example:
    `h.emails.reply_notifications.py`.
    """
    try:
        request.find_service(SubscriptionService).unsubscribe_using_token(
            token=request.matchdict["token"]
        )
    except InvalidUnsubscribeToken as err:
        raise HTTPNotFound() from err

    return {}
