# -*- coding: utf-8 -*-
import logging
import re
import sys

# XXX: Hack to ensure that submodule is patched when running under gevent.
# Remove this once h.script is updated to use gunicorn instead of pserve.
# Issue #1162
if 'gevent' in sys.modules:
    import gevent.subprocess
    sys.modules['subprocess'] = gevent.subprocess

from deform.field import Field
import pyramid

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


class WebassetsResourceRegistry(object):
    # pylint: disable=too-few-public-methods

    def __init__(self, env):
        self.env = env

    def __call__(self, requirements):
        result = {'js': [], 'css': []}

        urls = []
        for name, _ in requirements:
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
    # pylint: disable=too-few-public-methods

    def __init__(self, val, config):
        self.env = config.get_webassets_env()
        self.val = val

    def text(self):
        return 'asset_request = %s' % (self.val,)

    phash = text

    def __call__(self, event):
        request = event.request
        if request.matched_route is None:
            val = False
        else:
            val = request.matched_route.pattern.startswith(self.env.url)

        return self.val == val


def asset_response_subscriber(event):
    event.response.headers['Access-Control-Allow-Origin'] = '*'


def includeme(config):
    config.registry.settings.setdefault('webassets.bundles', 'assets.yaml')
    config.include('pyramid_webassets')

    # Set up a predicate and subscriber to set CORS headers on asset responses
    config.add_subscriber_predicate('asset_request', AssetRequest)
    config.add_subscriber(
        asset_response_subscriber,
        pyramid.events.NewResponse,
        asset_request=True
    )

    resource_registry = WebassetsResourceRegistry(config.get_webassets_env())
    Field.set_default_resource_registry(resource_registry)
    config.registry.resources = resource_registry
