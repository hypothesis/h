# -*- coding: utf-8 -*-
"""
:mod:`h.buildext` is a utility to build the Hypothesis browser extensions. It
is exposed as the command-line utility hypothesis-buildext.
"""

from __future__ import print_function

import argparse
import codecs
import json
import logging
import os
import os.path
import shutil
import sys

from jinja2 import Environment, PackageLoader

import h
from h import assets
from h import client
from h._compat import urlparse

jinja_env = Environment(loader=PackageLoader(__package__, ''))
log = logging.getLogger('h.buildext')

# Teach urlparse about extension schemes
urlparse.uses_netloc.append('chrome-extension')
urlparse.uses_relative.append('chrome-extension')
urlparse.uses_netloc.append('resource')
urlparse.uses_relative.append('resource')


class MissingSourceFile(Exception):
    pass


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


def copyfilelist(src, dst, filelist):
    """
    Copy a list of source files from src to dst.

    Raises MissingSourceFile if any of the files in the list are missing.
    """
    for path in filelist:
        srcpath = os.path.join(src, path)
        dstpath = os.path.join(dst, path)

        if not os.path.exists(srcpath):
            raise MissingSourceFile(srcpath)

        if not os.path.exists(os.path.dirname(dstpath)):
            os.makedirs(os.path.dirname(dstpath))

        shutil.copyfile(srcpath, dstpath)


def chrome_manifest(script_host_url, bouncer_url, browser):
    # Chrome is strict about the format of the version string
    if '+' in h.__version__:
        tag, detail = h.__version__.split('+')
        distance, commit = detail.split('.', 1)
        version = '{}.{}'.format(tag, distance)
        version_name = commit
    else:
        version = h.__version__
        version_name = 'Official Build'

    # If a bouncer URL was supplied, allow connections from the whole domain
    bouncer = urlparse.urljoin(bouncer_url, '*') if bouncer_url else None

    context = {
        'version': version,
        'version_name': version_name,
        'bouncer': bouncer,
        'browser': browser,
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


def build_extension(args):
    """
    Build the Chrome or Firefox extensions.

    You can supply the base URL of an h installation with which this extension
    will communicate, such as "http://localhost:5000" when developing locally or
    "https://hypothes.is" to talk to the production Hypothesis application.
    """
    service_url = args.service_url
    if not service_url.endswith('/'):
        service_url = '{}/'.format(service_url)

    build_dir = 'build/' + args.browser
    public_dir = os.path.join(build_dir, 'public')

    # Prepare a fresh build.
    clean(build_dir)
    os.makedirs(build_dir)
    os.makedirs(public_dir)

    # Bundle the extension assets.
    copytree('h/browser/chrome/content', os.path.join(build_dir, 'content'))
    copytree('h/browser/chrome/help', os.path.join(build_dir, 'help'))
    copytree('h/browser/chrome/images', os.path.join(build_dir, 'images'))
    copytree('h/static/images', os.path.join(public_dir, 'images'))
    copytree('h/static/styles/vendor/fonts', os.path.join(public_dir, 'fonts'))

    extension_sources = ['extension.bundle.js']
    if args.debug:
        extension_sources.extend([x + '.map' for x in extension_sources])

    client_sources = []
    env = assets.Environment('/public', 'h/assets.ini', 'build/manifest.json')
    for bundle in ['app_js', 'app_css', 'inject_js', 'inject_css']:
        client_sources.extend(env.files(bundle))
    if args.debug:
        client_sources.extend([x + '.map' for x in client_sources])

    try:
        copyfilelist(src='build/scripts',
                     dst=os.path.join(build_dir, 'lib'),
                     filelist=extension_sources)
        copyfilelist(src='h/browser/chrome/lib',
                     dst=os.path.join(build_dir, 'lib'),
                     filelist=['options.html', 'options.js'])
        copyfilelist(src='build',
                     dst=public_dir,
                     filelist=client_sources)
        copyfilelist(src='h/browser/chrome/lib',
                     dst=public_dir,
                     filelist=['destroy.js'])
    except MissingSourceFile as e:
        print("Missing source file: {:s}! Have you run `gulp build`?"
              .format(e))
        sys.exit(1)

    # Render the embed code.
    with codecs.open(os.path.join(public_dir, 'embed.js'), 'w', 'utf-8') as fp:
        data = client.render_embed_js(assets_env=env,
                                      app_html_url='/public/app.html')
        fp.write(data)

    # Render the sidebar html
    api_url = '{}api/'.format(service_url)
    with codecs.open(os.path.join(public_dir, 'app.html'), 'w', 'utf-8') as fp:
        data = client.render_app_html(
            api_url=api_url,
            service_url=service_url,
            # Google Analytics tracking is currently not enabled
            # for the extension
            ga_tracking_id=None,
            assets_env=env,
            websocket_url=args.websocket_url,
            sentry_public_dsn=args.sentry_public_dsn)
        fp.write(data)

    # Render the manifest.
    with codecs.open(os.path.join(build_dir, 'manifest.json'), 'w', 'utf-8') as fp:
        data = chrome_manifest(script_host_url=None,
                               bouncer_url=args.bouncer_url,
                               browser=args.browser)
        fp.write(data)

    # Write build settings to a JSON file
    with codecs.open(os.path.join(build_dir, 'settings-data.js'), 'w', 'utf-8') as fp:
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
parser.add_argument('--bouncer',
                    help='The URL of the direct-link bouncer service the '
                         'extension should use (e.g. "https://hpt.is/")',
                    dest='bouncer_url',
                    metavar='URL')
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
                    choices=['chrome', 'firefox'])


def main():
    args = parser.parse_args()
    build_extension(args)


if __name__ == '__main__':
    main()
