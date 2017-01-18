# -*- coding: utf-8 -*-
"""
Provides functions for building the assets for the Hypothesis client
application.
"""
import json
from h._compat import urlparse

from jinja2 import Environment, PackageLoader
from h import __version__

jinja_env = Environment(loader=PackageLoader(__package__, 'templates'))

def url_with_path(url):
    if urlparse.urlparse(url).path == '':
        return '{}/'.format(url)
    else:
        return url


def _app_html_context(assets_env, api_url, service_url, sentry_public_dsn,
                      websocket_url, ga_client_tracking_id):
    """
    Returns a dict of asset URLs and contents used by the sidebar app
    HTML tempate.
    """

    # the serviceUrl parameter must contain a path element
    service_url = url_with_path(service_url)

    app_config = {
        'apiUrl': api_url,
        'serviceUrl': service_url,
        'release': __version__
    }

    if websocket_url:
        app_config.update({
            'websocketUrl': websocket_url,
        })

    if sentry_public_dsn:
        app_config.update({
            'raven': {
                'dsn': sentry_public_dsn,
                'release': __version__
            }
        })

    if ga_client_tracking_id:
        app_config.update({
            'googleAnalytics': ga_client_tracking_id
        })

    return {
        'app_config': json.dumps(app_config),
        'app_css_urls': assets_env.urls('app_css'),
        'app_js_urls': assets_env.urls('app_js'),
    }


def render_app_html(assets_env,
                    service_url,
                    api_url,
                    sentry_public_dsn,
                    websocket_url=None,
                    ga_client_tracking_id=None,
                    extra=None):
    """
    Return the HTML for the Hypothesis app page,
    used by the sidebar, stream and single-annotation page.

    :param assets_env: The assets environment
    :param service_url: The base URL of the Hypothesis service
                     (eg. https://hypothes.is/)
    :param api_url: The root URL for the Hypothesis service API
    :param websocket_url: The WebSocket URL which the client should connect to
    :param sentry_public_dsn: The _public_ Sentry DSN for client-side
                              crash reporting
    :param ga_client_tracking_id: The Google Analytics tracking ID for the client
                  property.
    :param extra: A dict of optional properties specifying link tags and
                  meta attributes to be included on the page, passed through to
                  app.html.jinja2
    """
    template = jinja_env.get_template('app.html.jinja2')
    context = _app_html_context(api_url=api_url,
                                service_url=service_url,
                                sentry_public_dsn=sentry_public_dsn,
                                assets_env=assets_env,
                                websocket_url=websocket_url,
                                ga_client_tracking_id=ga_client_tracking_id).copy()
    if extra is not None:
        context.update(extra)
    return template.render(context)


def render_embed_js(assets_env, app_html_url, base_url=None):
    """
    Return the code for the script which is injected into a page in order
    to load the Hypothesis annotation client into it.

    :param assets_env: The assets environment
    :param app_html_url: The URL of the app.html page for the sidebar
    :param base_url: The absolute base URL of the web service
    """

    def absolute_asset_urls(bundle_name):
        return [urlparse.urljoin(base_url, url)
                for url in assets_env.urls(bundle_name)]

    template = jinja_env.get_template('embed.js.jinja2')
    template_args = {
        'app_html_url': app_html_url,
        'inject_resource_urls': absolute_asset_urls('inject_js') +
                                absolute_asset_urls('inject_css')
    }
    return template.render(template_args)
