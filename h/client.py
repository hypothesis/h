# -*- coding: utf-8 -*-
"""
Provides functions for building the assets for the Hypothesis client
application.
"""
import json
from urlparse import urlparse

from jinja2 import Environment, PackageLoader
from h import __version__

jinja_env = Environment(loader=PackageLoader(__package__, 'templates'))

ANGULAR_DIRECTIVE_TEMPLATES = [
    'annotation',
    'dropdown_menu_btn',
    'excerpt',
    'group_list',
    'login_form',
    'markdown',
    'publish_annotation_btn',
    'search_status_bar',
    'share_dialog',
    'sidebar_tutorial',
    'signin_control',
    'sort_dropdown',
    'thread',
    'top_bar',
    'viewer',
]


def _angular_template_context(name):
    """Return the context for rendering a 'text/ng-template' <script>
       tag for an Angular directive.
    """
    angular_template_path = 'client/{}.html'.format(name)
    content, _, _ = jinja_env.loader.get_source(jinja_env,
                                                angular_template_path)
    return {'name': '{}.html'.format(name), 'content': content}


def _merge(d1, d2):
    result = d1.copy()
    result.update(d2)
    return result


def websocketize(value):
    """Convert a HTTP(S) URL into a WS(S) URL."""
    if not (value.startswith('http://') or value.startswith('https://')):
        raise ValueError('cannot websocketize non-HTTP URL')
    return 'ws' + value[len('http'):]


def asset_urls(webassets_env, name):
    return webassets_env[name].urls()


def url_with_path(url):
    if urlparse(url).path == '':
        return '{}/'.format(url)
    else:
        return url


def _app_html_context(webassets_env, api_url, base_url, ga_tracking_id,
                      sentry_dsn, websocket_url):
    """
    Returns a dict of asset URLs and contents used by the sidebar app
    HTML tempate.
    """

    if urlparse(base_url).hostname == 'localhost':
        ga_cookie_domain = 'none'
    else:
        ga_cookie_domain = 'auto'

    # the serviceUrl parameter must contain a path element
    base_url = url_with_path(base_url)

    app_config = {
        'apiUrl': api_url,
        'serviceUrl': base_url,
        'websocketUrl': websocket_url,
    }

    if sentry_dsn:
        app_config.update({
            'raven': {
                'dsn': sentry_dsn,
                'release': __version__
            }
        })

    return {
        'app_config': json.dumps(app_config),
        'angular_templates': map(_angular_template_context,
                                 ANGULAR_DIRECTIVE_TEMPLATES),
        'app_css_urls': asset_urls(webassets_env, 'app_css'),
        'app_js_urls': asset_urls(webassets_env, 'app_js'),
        'base_url': base_url,
        'ga_tracking_id': ga_tracking_id,
        'ga_cookie_domain': ga_cookie_domain,
        'register_url': base_url + 'register',
    }


def render_app_html(webassets_env,
                    base_url,
                    api_url,
                    websocket_url,
                    sentry_dsn,
                    ga_tracking_id=None,
                    extra={}):
    """
    Return the HTML for the Hypothesis app page,
    used by the sidebar, stream and single-annotation page.

    :param base_url: The base URL of the Hypothesis service
                     (eg. https://hypothes.is/)
    :param api_url: The root URL for the Hypothesis service API
    :param websocket_url: The WebSocket URL which the client should connect to
    :param sentry_dsn: The _public_ Sentry DSN for client-side crash reporting
    :param ga_tracking_id: The Google Analytics tracking ID
    :param extra: A dict of optional properties specifying link tags and
                  meta attributes to be included on the page, passed through to
                  app.html.jinja2
    """
    template = jinja_env.get_template('app.html.jinja2')
    assets_dict = _app_html_context(api_url=api_url,
                                    base_url=base_url,
                                    ga_tracking_id=ga_tracking_id,
                                    sentry_dsn=sentry_dsn,
                                    webassets_env=webassets_env,
                                    websocket_url=websocket_url)
    return template.render(_merge(assets_dict, extra))


def render_embed_js(webassets_env, app_html_url):
    """
    Return the code for the script which is injected into a page in order
    to load the Hypothesis annotation client into it.

    :param app_html_url: The URL of the app.html page for the sidebar
    """
    template = jinja_env.get_template('embed.js.jinja2')
    template_args = {
        'app_html_url': app_html_url,
        'inject_js_urls': asset_urls(webassets_env, 'inject'),
        'wgxpath_url': asset_urls(webassets_env, 'wgxpath')[0],
    }
    return template.render(template_args)
