# -*- coding: utf-8 -*-
import re

from deform.field import Field
from webassets.filter import ExternalTool, register_filter
import pyramid


class Browserify(ExternalTool):
    """
    An input filter for webassets that browserifies CoffeeScript or JavaScript.
    """
    name = 'browserify'
    options = {
        'binary': 'BROWSERIFY_BIN',
        'extra_args': 'BROWSERIFY_EXTRA_ARGS',
    }
    extra_args = None
    max_debug_level = None

    def input(self, in_, out, **kwargs):
        args = [self.binary or 'browserify']

        args.append(kwargs['source_path'])

        if self.get_config('debug'):
            args.append('-d')

        if self.extra_args is not None:
            if isinstance(self.extra_args, basestring):
                self.extra_args = self.extra_args.split()
            args.extend(self.extra_args)

        self.subprocess(args, out)

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


def setup_jinja2_enviroment(config):
    jinja2_env = config.get_jinja2_environment('__webassets__')
    jinja2_env.globals['feature'] = config.feature
    jinja2_env.variable_start_string = '"{{'
    jinja2_env.variable_end_string = '}}"'

    webassets_env = config.get_webassets_env()
    webassets_env.config['jinja2_env'] = jinja2_env


def includeme(config):
    config.registry.settings.setdefault('webassets.bundles', 'h:assets.yaml')
    config.include('pyramid_webassets')

    config.include('pyramid_jinja2')
    config.add_jinja2_renderer('__webassets__')
    config.action(None, setup_jinja2_enviroment, args=(config,), order=1)

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
