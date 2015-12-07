"""The home/front page of the //hypothes.is/ site."""
from pyramid import view

from datetime import datetime
import email.utils
import requests
import xml.etree.ElementTree as ElementTree


# in-memory cache of the most recently fetched N
# Hypothesis blog posts
news_items = []
news_item_last_fetch = None


# maximum age of the RSS feed cache in seconds
MAX_FEED_CACHE_AGE = 60 * 10


# TODO - Move this to a sensible location, add tests
def fetch_recent_blog_items(max_items):
    """ Fetches the most recent :max_items: from the Hypothesis blog.

    :returns: A dictionary containing the title, formatted date and snippet
              for the most recent items.
    """
    rss = requests.get('https://hypothes.is/feed')
    rss_xml = rss.text.encode('utf-8')
    recent_items = ElementTree.fromstring(rss_xml).findall('*/item')
    parsed_items = []
    for item in recent_items[0:max_items]:
        # parse date in RFC 822 format and convert to
        # <Month> DD YYYY
        # (note this relies on support for dashes in format specifiers to avoid
        #  zero-padding the day, see http://stackoverflow.com/questions/28894172/)
        date = email.utils.parsedate(item.find('pubDate').text)
        formatted_date = datetime(*date[0:3]).strftime('%B %-d, %Y')

        parsed_items.append({
            "title": item.find('title').text,
            "link": item.find('link').text,
            "date": formatted_date,
            "snippet": item.find('description').text,
        })

    return parsed_items


def refresh_news_item_cache():
    global news_item_last_fetch
    global news_items

    if len(news_items) == 0 or \
       (datetime.now() - news_item_last_fetch).seconds > MAX_FEED_CACHE_AGE:

        try:
            news_items = fetch_recent_blog_items(max_items=3)
            news_item_last_fetch = datetime.now()
        except Exception as ex:
            # TODO - Log an error and leave the existing items unchanged
            pass


@view.view_config(route_name='index',
                  request_method='GET',
                  renderer='h:templates/home.html.jinja2')
def index(context, request):
    refresh_news_item_cache()

    config = {
        "chrome_ext_link": "https://chrome.google.com/webstore/detail/bjfhmglciegochdpefhhlphglcehbmek",
        "rss_feed_url": "https://hypothes.is/feed",
        "news_items": news_items,
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
