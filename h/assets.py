from os import path
from urlparse import urlparse

import re
import sys

if 'gevent' in sys.modules:
    import gevent.subprocess
    sys.modules['subprocess'] = gevent.subprocess

import pyramid

from webassets.filter import register_filter
from webassets.filter.cssrewrite import urlpath
from webassets.filter.cssrewrite.base import CSSUrlRewriter
from webassets.loaders import YAMLLoader

import logging
log = logging.getLogger(__name__)


class CSSVersion(CSSUrlRewriter):
    """Source filter to resolve urls in CSS files using the asset resolver.

    The 'cssrewrite' filter supplied with webassets will rewrite relative
    URLs in the CSS so that they are relative to the output path of the
    file so that paths are correct after merging CSS files from different
    sources. This filter is designed to run after that in order to resolve
    these URLs using the configured resolver so that the assets include
    version information even when referenced from the CSS.
    """

    name = 'cssversion'
    max_debug_level = 'merge'

    def replace_url(self, url):
        parsed = urlparse(url)
        if parsed.scheme:
            return url
        else:
            dirname = path.dirname(self.output_path)
            filepath = path.join(dirname, parsed.path)
            filepath = path.normpath(path.abspath(filepath))
            resolved = self.env.resolver.resolve_source_to_url(filepath, url)
            relative = urlpath.relpath(self.output_url, resolved)
            return relative


class WebassetsResourceRegistry(object):
    def __init__(self, env):
        self.env = env

    def __call__(self, requirements):
        result = {'js': [], 'css': []}

        urls = []
        for name in zip(*requirements)[0]:
            log.info('name: ' + str(name))
            if name in self.env:
                bundle = self.env[name]
                urls.extend(bundle.urls())

        for source in urls:
            # check asset type (js or css), modulo cache-busting qs
            for thing in ('js', 'css'):
                if re.search(r'\.%s(\??[^/]+)?$' % thing, source):
                    if not source in result[thing]:
                        result[thing].append(source)

        return result


class AssetRequest(object):
    def __init__(self, val, config):
        self.env = config.get_webassets_env()
        self.val = val

    def text(self):
        return 'asset_request = %s' % (self.val,)

    phash = text

    def __call__(self, event):
        request = event.request
        if request.matched_route is None:
            return False
        else:
            return request.matched_route.pattern.startswith(self.env.url)


def asset_response_subscriber(event):
    event.response.headers['Access-Control-Allow-Origin'] = '*'


def includeme(config):
    config.include('pyramid_webassets')
    register_filter(CSSVersion)


    # Set up a predicate and subscriber to set CORS headers on asset responses
    config.add_subscriber_predicate('asset_request', AssetRequest)
    config.add_subscriber(
        asset_response_subscriber,
        pyramid.events.NewResponse,
        asset_request=True
    )

    assets_file = config.registry.settings.get('assets', 'assets.yaml')
    loader = YAMLLoader(assets_file)
    bundles = loader.load_bundles()
    for bundle_name in bundles:
        log.info('name: ' + str(bundle_name))
        config.add_webasset(bundle_name, bundles[bundle_name])

    from deform.field import Field
    resource_registry = WebassetsResourceRegistry(config.get_webassets_env())
    Field.set_default_resource_registry(resource_registry)
    config.registry.resources = resource_registry
