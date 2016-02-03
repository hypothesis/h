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

from jinja2 import Environment, PackageLoader
from pyramid.path import AssetResolver
import webassets
from webassets.loaders import YAMLLoader

import h
# h.assets provides webassets filters for JS and CSS compilation
import h.assets
from h import client
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
    """
    Asset path resolver for webassets which can resolve package-relative paths.

    This resolver supports the <package>:<path> path specifiers
    (eg. 'h:path/to/asset.css') which are used in assets.yaml.
    """

    def search_for_source(self, ctx, item):
        if item.startswith('../'):
            # When building assets outside of the root 'h/static' directory,
            # webassets puts the results in
            # `h/static/webassets-external/[MD5_HASH_OF_PATH]_filename` where
            # MD5_HASH_OF_PATH is a hash of the absolute, non-canonicalized
            # path (ie. still containing any '../../' from the item path
            # in assets.yaml)
            #
            # When building in development mode where embed.js is included in
            # the Chrome extension but other JS files are not, the webassets
            # environment in buildext.py needs to generate the same URLs for
            # vendor JS files referenced in embed.js as the '/embed.js'
            # route in the main app, so that the MD5 hashes match.
            return '{}/{}'.format(resolve('h:static').abspath(), item)
        else:
            return resolve(item).abspath()


def build_extension_common(webassets_env, service_url, bundle_app=False):
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
            app_html_url = '/public/app.html'
        else:
            app_html_url = '{}app.html'.format(service_url)

        data = client.render_embed_js(webassets_env=webassets_env,
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
        'version': version,
        'version_name': version_name
    }

    if script_host_url:
        context['script_src'] = script_host_url

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


def settings_dict(service_url, api_url, sentry_public_dsn):
    """ Returns a dictionary of settings to be bundled with the extension """
    config = {
        'apiUrl': api_url,
        'buildType': build_type_from_api_url(api_url),
        'serviceUrl': service_url,
    }

    if sentry_public_dsn:
        config.update({
            'raven': {
                'dsn': sentry_public_dsn,
                'release': h.__version__,
            },
        })

    return config


def get_webassets_env(base_dir, assets_url, debug=False):
    """
    Get a webassets environment configured for building browser extensions.

    :param base_dir: The directory into which the assets should be built.
    :param assets_url: The relative or absolute URL used to reference assets
                       in the app.html and embed.js files.
    :param debug: If true, generates source maps and skips minification.
    """
    webassets_env = webassets.Environment(
        directory=os.path.abspath(base_dir),
        url=assets_url)

    # Disable webassets caching and manifest generation
    webassets_env.cache = False
    webassets_env.manifest = False
    webassets_env.resolver = Resolver()
    webassets_env.config['UGLIFYJS_BIN'] = './node_modules/.bin/uglifyjs'
    webassets_env.debug = debug

    loader = YAMLLoader(resolve('h:assets.yaml').abspath())
    webassets_env.register(loader.load_bundles())

    return webassets_env


def build_chrome(args):
    """
    Build the Chrome extension. You can supply the base URL of an h
    installation with which this extension will communicate, such as
    "http://localhost:5000" when developing locally or
    "https://hypothes.is" to talk to the production Hypothesis application.
    """
    service_url = args.service_url
    if not service_url.endswith('/'):
        service_url = '{}/'.format(service_url)

    webassets_env = get_webassets_env(base_dir='./build/chrome/public',
                                      assets_url='/public',
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
    api_url = '{}api/'.format(service_url)

    if args.bundle_sidebar:
        build_extension_common(webassets_env, service_url, bundle_app=True)
        with codecs.open(content_dir + '/app.html', 'w', 'utf-8') as fp:
            data = client.render_app_html(
                api_url=api_url,
                service_url=service_url,

                # Google Analytics tracking is currently not enabled
                # for the extension
                ga_tracking_id=None,
                webassets_env=webassets_env,
                websocket_url=args.websocket_url,
                sentry_public_dsn=args.sentry_public_dsn)
            fp.write(data)
    else:
        build_extension_common(webassets_env, service_url)

    # Render the manifest.
    with codecs.open('build/chrome/manifest.json', 'w', 'utf-8') as fp:
        script_url = urlparse.urlparse(webassets_env.url)
        if script_url.scheme and script_url.netloc:
            script_host_url = '{}://{}'.format(script_url.scheme,
                                               script_url.netloc)
        else:
            script_host_url = None
        data = chrome_manifest(script_host_url)
        fp.write(data)

    # Write build settings to a JSON file
    with codecs.open('build/chrome/settings-data.js', 'w', 'utf-8') as fp:
        settings = settings_dict(service_url, api_url, args.sentry_public_dsn)
        fp.write('window.EXTENSION_CONFIG = ' + json.dumps(settings))


def check_sentry_dsn_is_public(dsn):
    parsed_dsn = urlparse.urlparse(dsn)
    if parsed_dsn.password:
        raise argparse.ArgumentTypeError(
            "Must be a public Sentry DSN which does not contain a secret key.")
    return dsn


parser = argparse.ArgumentParser('hypothesis-buildext')
parser.add_argument('--debug',
                    action='store_true',
                    default=False,
                    help='create source maps to enable debugging in browser')
parser.add_argument('--sentry-public-dsn',
                    default='',
                    help='Specify the public Sentry DSN for crash reporting',
                    metavar='DSN',
                    type=check_sentry_dsn_is_public)
parser.add_argument('--service',
                    help='The URL of the Hypothesis service which the '
                    'extension should connect to',
                    default='https://hypothes.is/',
                    dest='service_url',
                    metavar='URL')
parser.add_argument('--websocket',
                    help='The URL of the websocket endpoint which the '
                    'extension should connect to (e.g. '
                    '"wss://hypothes.is/ws")',
                    dest='websocket_url',
                    metavar='URL')
parser.add_argument('--no-bundle-sidebar',
                    action='store_false',
                    dest='bundle_sidebar',
                    help='Use the sidebar from the Hypothesis service instead'
                         ' of building it into the extension')
parser.add_argument('browser',
                    help='Specifies the browser to build an extension for',
                    choices=['chrome'])

BROWSERS = {'chrome': build_chrome}


def main():
    args = parser.parse_args()
    BROWSERS[args.browser](args)


if __name__ == '__main__':
    main()
