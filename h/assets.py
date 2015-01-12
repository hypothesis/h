# -*- coding: utf-8 -*-
import re

from deform.field import Field
from webassets.filter import ExternalTool, register_filter
import pyramid


class Browserify(ExternalTool):
    """
    An input filter for webassets that browserifies CoffeeScript or JavaScript.

    The browserify command-line client has several limitations when piping
    input to STDIN:

    - it uses a dummy name for the piped file in sourcemaps
    - because it does not know the real name of the piped file, it cannot
      accept CoffeeScript, because it does not know the real extension of the
      piped file

    The filter uses the browserify-pipe tool, shipped in ``tools/`` in the
    repository root, which circumvents these issues.
    """
    name = 'browserify'
    options = {'binary': 'BROWSERIFY_PIPE_BIN'}
    max_debug_level = None

    def input(self, in_, out, source_path, **kwargs):
        args = [self.binary or 'browserify-pipe']

        if self.get_config('debug'):
            args.append('-d')

        args.append(source_path)
        self.subprocess(args, out, in_)

register_filter(Browserify)


class WebassetsResourceRegistry(object):

    def __init__(self, env):
        self.env = env

    def __call__(self, requirements):
        result = {'js': [], 'css': []}

        urls = []
        for name, _ in requirements:
            if name in self.env:
                bundle = self.env[name]
                urls.extend(bundle.urls())

        for source in urls:
            # check asset type (js or css), modulo cache-busting qs
            for thing in ('js', 'css'):
                if re.search(r'\.%s(\??[^/]+)?$' % thing, source):
                    if source not in result[thing]:
                        result[thing].append(source)

        return result


class AssetRequest(object):
    """A subscriber predicate that checks whether a route is a static asset.

    This predicate relies on the facto that static assets registered via
    :meth:`pyramid.config.Configurator.add_static_view` are prefixed with
    a double underscore. While this approach seems brittle, it works (provided
    users don't register their own views this way) and it supports all static
    view requests (not just those registered by pyramid_webassets).
    """

    def __init__(self, val, config):
        self.val = val

    def text(self):
        return 'asset_request = %s' % (self.val,)

    phash = text

    def __call__(self, event):
        request = event.request
        if request.matched_route is None:
            val = False
        else:
            val = request.matched_route.name.startswith('__')

        return self.val == val


def asset_response_subscriber(event):
    event.response.headers['Access-Control-Allow-Origin'] = '*'


def includeme(config):
    config.registry.settings.setdefault('webassets.bundles', 'h:assets.yaml')
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
