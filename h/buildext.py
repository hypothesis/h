# -*- coding: utf-8 -*-
"""
:mod:`h.buildext` is a utility to build the Hypothesis browser extensions. It
is exposed as the command-line utility hypothesis-buildext.
"""
import argparse
import codecs
import json
import logging
import os
import os.path
import shutil
import subprocess
import textwrap

from jinja2 import Environment, PackageLoader
from pyramid.path import AssetResolver
import raven
import webassets
from webassets.loaders import YAMLLoader

import h
# h.assets provides webassets filters for JS and CSS compilation
import h.assets
from h import client
from h.client import url_with_path, websocketize
from h._compat import urlparse

jinja_env = Environment(loader=PackageLoader(__package__, ''))
log = logging.getLogger('h.buildext')

# Teach urlparse about extension schemes
urlparse.uses_netloc.append('chrome-extension')
urlparse.uses_relative.append('chrome-extension')
urlparse.uses_netloc.append('resource')
urlparse.uses_relative.append('resource')

# Fetch an asset spec resolver
resolve = AssetResolver().resolve


class Resolver(webassets.env.Resolver):
    """A custom resolver for webassets which can resolve
       package-relative paths (eg. 'h:path/to/asset.css') that are used
       in assets.yaml
    """

    def search_for_source(self, ctx, item):
        if item.startswith('../'):
            # relative URLs in assets.yaml are relative to h/static
            # Note that the return path here is not canonicalized
            # (ie. '../' is not removed) for consistency with the way
            # webassets resolves paths in the main app.
            #
            # This can be removed once webassets is replaced with a better
            # system for client asset generation
            return '{}/{}'.format(resolve('h:static').abspath(), item)
        else:
            return resolve(item).abspath()


def build_extension_common(webassets_env, base_url, bundle_app=False):
    """
    Copy the contents of src to dest, including some generic extension scripts.
    """
    # Create the assets directory
    content_dir = webassets_env.directory

    # Copy over the config and destroy scripts
    shutil.copyfile('h/static/extension/destroy.js',
                    content_dir + '/destroy.js')
    shutil.copyfile('h/static/extension/config.js', content_dir + '/config.js')

    # Render the embed code.
    with codecs.open(content_dir + '/embed.js', 'w', 'utf-8') as fp:
        if bundle_app:
            app_html_url = webassets_env.url + '/app.html'
        else:
            app_html_url = '{}/app.html'.format(base_url)

        data = client_assets.render_embed_js(webassets_env=webassets_env,
                                             app_html_url=app_html_url)
        fp.write(data)


def clean(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def copytree(src, dst):
    """
    Copy a tree from src to dst, without complaining if dst already contains
    some directories in src like :func:`shutil.copytree`.

    Behaves identically to ``cp src/* dst/``.
    """
    if not os.path.exists(dst):
        os.mkdir(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d)
        else:
            shutil.copyfile(s, d)


def chrome_manifest(script_host_url):
    # Chrome is strict about the format of the version string
    if '+' in h.__version__:
        tag, detail = h.__version__.split('+')
        distance, commit = detail.split('.', 1)
        version = '{}.{}'.format(tag, distance)
        version_name = commit
    else:
        version = h.__version__
        version_name = 'Official Build'

    context = {
        'script_src': script_host_url,
        'version': version,
        'version_name': version_name
    }

    template = jinja_env.get_template('browser/chrome/manifest.json.jinja2')
    return template.render(context)


def build_type_from_api_url(api_url):
    """
    Returns the default build type ('production', 'staging' or 'dev')
    when building an extension that communicates with the given service
    """
    host = urlparse.urlparse(api_url).netloc
    if host == 'hypothes.is':
        return 'production'
    elif host == 'stage.hypothes.is':
        return 'staging'
    else:
        return 'dev'


def settings_dict(base_url, api_url, sentry_dsn):
    """ Returns a dictionary of settings to be bundled with the extension """
    config = {
        'apiUrl': api_url,
        'buildType': build_type_from_api_url(api_url),
        'serviceUrl': url_with_path(base_url),
    }

    if sentry_dsn:
        config.update({
            'raven': {
                'dsn': sentry_dsn,
                'release': h.__version__,
            },
        })

    return config


def get_webassets_env(base_dir, base_url, assets_url, debug=False):
    webassets_env = webassets.Environment(
        directory=os.path.abspath('./build/chrome/public'),
        url=assets_url or '{}/assets'.format(base_url))

    # Disable webassets caching and manifest generation
    webassets_env.cache = False
    webassets_env.manifest = False
    webassets_env.resolver = Resolver()
    webassets_env.config['UGLIFYJS_BIN'] = './node_modules/.bin/uglifyjs'
    webassets_env.debug = debug

    # By default, webassets will use its base_dir setting as its search path.
    # When building extensions, we change base_dir so as to build assets
    # directly into the extension directories. As a result, we have to add
    # back the correct search path.
    webassets_env.append_path(resolve('h:static').abspath(), webassets_env.url)
    loader = YAMLLoader(resolve('h:assets.yaml').abspath())
    webassets_env.register(loader.load_bundles())

    return webassets_env


def build_chrome(args):
    """
    Build the Chrome extension. You can supply the base URL of an h
    installation with which this extension will communicate, such as
    "http://localhost:5000" (the default) when developing locally or
    "https://hypothes.is" to talk to the production Hypothesis application.

    By default, the extension will load static assets (JavaScript/CSS/etc.)
    from the application you specify. This can be useful when developing, but
    when building a production extension for deployment to the Chrome Store you
    will need to specify an assets URL that links to the built assets within
    the Chrome Extension, such as:

        chrome-extension://<extensionid>/public
    """
    base_url = args.base
    if base_url.endswith('/'):
        base_url = base_url[:-1]

    webassets_env = get_webassets_env(base_dir='./build/chrome/public',
                                      base_url=base_url,
                                      assets_url=args.assets,
                                      debug=args.debug)

    # Prepare a fresh build.
    clean('build/chrome')
    os.makedirs('build/chrome')
    content_dir = webassets_env.directory
    os.makedirs(content_dir)

    # Bundle the extension assets.
    copytree('h/browser/chrome/content', 'build/chrome/content')
    copytree('h/browser/chrome/help', 'build/chrome/help')
    copytree('h/browser/chrome/images', 'build/chrome/images')
    copytree('h/static/images', 'build/chrome/public/images')

    os.makedirs('build/chrome/lib')

    subprocess_args = ['node_modules/.bin/browserify',
                       'h/browser/chrome/lib/extension.js', '--outfile',
                       'build/chrome/lib/extension-bundle.js']
    if args.debug:
        subprocess_args.append('--debug')
    subprocess.call(subprocess_args)

    # Render the sidebar html
    api_url = '{}/api'.format(base_url)
    websocket_url = websocketize('{}/ws'.format(base_url))
    register_url = '{}/register'.format(base_url)
    sentry_dsn = None

    if args.sentry_dsn:
        sentry_dsn = raven.Client(args.sentry_dsn).get_public_dsn()
        if (sentry_dsn.startswith('//')):
            # the Raven client generates schemeless public DSNs by default,
            # but we're running code in a page served from a 'chrome-extension:'
            # URL, so we need to specify the scheme explicitly
            sentry_dsn = 'https:'.format(sentry_dsn)

    if webassets_env.url.startswith('chrome-extension:'):
        build_extension_common(webassets_env, base_url, bundle_app=True)
        with codecs.open(content_dir + '/app.html', 'w', 'utf-8') as fp:
            data = client_assets.render_app_html(
                api_url=api_url,
                base_url=url_with_path(base_url),

                # Google Analytics tracking is currently not enabled
                # for the extension
                ga_tracking_id=None,
                register_url=register_url,
                webassets_env=webassets_env,
                websocket_url=websocket_url,
                sentry_dsn=sentry_dsn)
            fp.write(data)
    else:
        build_extension_common(webassets_env, base_url)

    # Render the manifest.
    with codecs.open('build/chrome/manifest.json', 'w', 'utf-8') as fp:
        script_url = urlparse.urlparse(webassets_env.url)
        script_host_url = '{}://{}'.format(script_url.scheme,
                                           script_url.netloc)
        data = chrome_manifest(script_host_url)
        fp.write(data)

    # Write build settings to a JSON file
    with codecs.open('build/chrome/settings-data.js', 'w', 'utf-8') as fp:
        settings = settings_dict(base_url, api_url, sentry_dsn)
        fp.write('window.EXTENSION_CONFIG = ' + json.dumps(settings))


parser = argparse.ArgumentParser('hypothesis-buildext')
parser.add_argument('--debug',
                    action='store_true',
                    default=False,
                    help='create source maps to enable debugging in browser')
parser.add_argument('--sentry-dsn',
                    default='',
                    help='Specify the Sentry DSN for crash reporting',
                    metavar='SENTRY_DSN')
parser.add_argument('--base',
                    help='Base URL',
                    default='http://localhost:5000',
                    metavar='URL')
parser.add_argument('--assets',
                    help='A path (relative to base) or URL from which '
                    'to load the static assets',
                    default=None,
                    metavar='PATH/URL')
parser.add_argument('browser',
                    help='Specifies the browser to build an extension for',
                    choices=['chrome'])

BROWSERS = {'chrome': build_chrome}


def main():
    args = parser.parse_args()
    BROWSERS[args.browser](args)


if __name__ == '__main__':
    main()
