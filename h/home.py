"""The home/front page of the //hypothes.is/ site."""
from pyramid import view


@view.view_config(route_name='index',
                  request_method='GET',
                  renderer='h:templates/home.html.jinja2')
def index(context, request):
    config = {
        "chrome_ext_link": "https://chrome.google.com/webstore/detail/bjfhmglciegochdpefhhlphglcehbmek",
        "rss_feed_url": "https://hypothes.is/feed",
    }

    if request.authenticated_user:
        username = request.authenticated_user.username
        user_profile_link = (
            request.route_url("stream")
            + "?q=user:{username}".format(username=username))
        config.update({
            "username": username,
            "user_profile_link": user_profile_link,
        })

    return config


def includeme(config):
    config.add_route('index', '/')
    config.scan(__name__)
