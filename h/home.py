"""The home/front page of the //hypothes.is/ site."""
from pyramid import view


def trim_snippet(snippet):
    MAX_SNIPPET_LENGTH = 190
    return snippet[0:MAX_SNIPPET_LENGTH] + u"\u2026"


# recent blog posts on the H blog from 7/12/15 for the initial
# implementation of the new homepage design. This will be followed
# up by a proper system for fetching posts and caching them.
RECENT_NEWS_ITEMS = [{
    "title": "A Coalition of over 40 Scholarly Publishers",
    "link": "https://hypothes.is/blog/a-coalition-of-over-40-scholarly-publishers/",
    "date": "December 1, 2015",
    "snippet": trim_snippet("""
Today we're announcing a coalition of over 40 scholarly publishers, platforms,
libraries and technology partners that share the goal of building an open
conversation layer over all knowledge. Over the next several years this coalition
will be working together to define, design and implement a common framework for
scholarly collaboration from peer-review through post-publication discussion
""")
},{
    "title": "Undergrad Shannon Griffiths on Using Hypothesis in the Classroom",
    "link": "https://hypothes.is/blog/undergrad-shannon-griffiths-on-using-hypothesis-in-the-classroom/",
    "date": "November 30, 2015",
    "snippet": trim_snippet("""
This blog was written and published by Shannon Griffiths, an English major at
Plymouth State University. Her professor, Robin DeRosa, is using Hypothesis in
several of her classes this term. Check out her Open Anthology of
Earlier American Literature, hosted on PressBooks and
annotated using Hypothesis by her undergraduates.""")
},{
    "title": "Hypothes.is at Society for Neuroscience",
    "link": "https://hypothes.is/blog/hypothes-is-at-society-for-neuroscience/",
    "date": "November 19, 2015",
    "snippet": trim_snippet("""
At long last, I'm able to sit down and summarize my thoughts and experiences on
Hypothes.is at the Society for Neuroscience meeting in Chicago, Oct 17-21st.
First of all, a hearty, gigantic thank you to my colleagues at the
Neuroscience Information Framework, a Hypothes.is partner
""")
}]


@view.view_config(route_name='index',
                  request_method='GET',
                  renderer='h:templates/home.html.jinja2')
def index(context, request):
    config = {
        "chrome_ext_link": "https://chrome.google.com/webstore/detail/bjfhmglciegochdpefhhlphglcehbmek",
        "rss_feed_url": "https://hypothes.is/feed",
        "news_items": RECENT_NEWS_ITEMS,
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
