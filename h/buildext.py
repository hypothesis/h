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


class AssetBundle(object):
    def __init__(self, env, files):
        self._env = env
        self._files = files

    def urls(self):
        def asset_url(path):
            return '{}/{}'.format(self._env._prefix, path)

        return map(asset_url, self._files)

    def files(self):
        return self._files


class AssetEnvironment(object):
    """
    A minimal implementation of webassets.Environment.

    This is a simplified version of webassets.Environment used for
    rendering the app.html and embed.js files bundled with the extension.
    """
    def __init__(self, prefix):
        self._bundles = {}
        self._prefix = prefix

    def register(self, bundle_name, files):
        self._bundles[bundle_name] = AssetBundle(self, files)

    def __getitem__(self, item):
        return self._bundles[item]


def build_extension_common(content_dir, webassets_env,
                           service_url, bundle_app=False):
    """
    Copy the contents of src to dest, including some generic extension scripts.
    """
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

    # Prepare a fresh build.
    clean('build/chrome')
    os.makedirs('build/chrome')
    content_dir = 'build/chrome/public'
    os.makedirs(content_dir)

    # Bundle the extension assets.
    copytree('h/browser/chrome/content', 'build/chrome/content')
    copytree('h/browser/chrome/help', 'build/chrome/help')
    copytree('h/browser/chrome/images', 'build/chrome/images')
    copytree('h/static/images', 'build/chrome/public/images')
    copytree('h/static/styles/vendor/fonts', 'build/chrome/public/fonts')

    subprocess_args = ['node_modules/.bin/gulp', 'build']
    subprocess.call(subprocess_args)

    os.makedirs('build/chrome/lib')
    shutil.copyfile('build/scripts/extension.bundle.js',
                    'build/chrome/lib/extension.bundle.js')
    if args.debug:
        shutil.copyfile('build/scripts/extension.bundle.js.map',
                        'build/chrome/lib/extension.bundle.js.map')

    webassets_env = AssetEnvironment('/public')
    webassets_env.register('app_js', [
        'scripts/raven.bundle.js',
        'scripts/angular.bundle.js',
        'scripts/katex.bundle.js',
        'scripts/showdown.bundle.js',
        'scripts/polyfills.bundle.js',
        'scripts/unorm.bundle.js',
        'scripts/app.bundle.js',
    ])

    webassets_env.register('app_css', [
        'styles/angular-csp.css',
        'styles/angular-toastr.css',
        'styles/icomoon.css',
        'styles/katex.min.css',
        'styles/app.css',
    ])

    webassets_env.register('inject_js', [
        'scripts/jquery.bundle.js',
        'scripts/injector.bundle.js',
    ])

    webassets_env.register('inject_css', [
        'styles/icomoon.css',
        'styles/inject.css',
        'styles/pdfjs-overrides.css',
    ])

    for bundle in ['app_js', 'app_css', 'inject_js', 'inject_css']:
        for path in webassets_env[bundle].files():
            dest_path = '{}/{}'.format(content_dir, path)
            dest_dir = os.path.dirname(dest_path)

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copyfile('build/{}'.format(path), dest_path)

            sourcemap_path = '{}.map'.format(path)
            sourcemap_dest_path = '{}/{}'.format(content_dir, sourcemap_path)

            if args.debug:
                shutil.copyfile('build/{}'.format(sourcemap_path),
                                sourcemap_dest_path)

    # Render the sidebar html
    api_url = '{}api/'.format(service_url)
    build_extension_common(content_dir, webassets_env,
                           service_url, bundle_app=True)
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

    # Render the manifest.
    with codecs.open('build/chrome/manifest.json', 'w', 'utf-8') as fp:
        data = chrome_manifest(script_host_url=None)
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
parser.add_argument('browser',
                    help='Specifies the browser to build an extension for',
                    choices=['chrome'])

BROWSERS = {'chrome': build_chrome}


def main():
    args = parser.parse_args()
    BROWSERS[args.browser](args)


if __name__ == '__main__':
    main()
