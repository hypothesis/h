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

from pyramid import paster
from pyramid.path import AssetResolver
from pyramid.renderers import render
from pyramid.request import Request
import raven

import h
from h._compat import urlparse
from h.sidebar import app_config


log = logging.getLogger('h.buildext')

# Teach urlparse about extension schemes
urlparse.uses_netloc.append('chrome-extension')
urlparse.uses_relative.append('chrome-extension')
urlparse.uses_netloc.append('resource')
urlparse.uses_relative.append('resource')

# Fetch an asset spec resolver
resolve = AssetResolver().resolve


def build_extension_common(env, bundle_app=False):
    """
    Copy the contents of src to dest, including some generic extension scripts.
    """
    # Create the assets directory
    request = env['request']
    content_dir = request.webassets_env.directory

    # Copy over the config and destroy scripts
    shutil.copyfile('h/static/extension/destroy.js',
                    content_dir + '/destroy.js')
    shutil.copyfile('h/static/extension/config.js',
                    content_dir + '/config.js')

    # Render the embed code.
    with codecs.open(content_dir + '/embed.js', 'w', 'utf-8') as fp:
        if bundle_app:
            app_uri = request.webassets_env.url + '/app.html'
        else:
            app_uri = request.route_url('widget')
        value = {'app_uri': app_uri}
        data = render('h:templates/embed.js.jinja2', value, request=request)
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


def chrome_manifest(request):
    # Chrome is strict about the format of the version string
    if '+' in h.__version__:
        tag, detail = h.__version__.split('+')
        distance, commit = detail.split('.', 1)
        version = '{}.{}'.format(tag, distance)
        version_name = commit
    else:
        version = h.__version__
        version_name = 'Official Build'

    src = request.resource_url(request.context)

    # We need to use only the host and port for the CSP script-src when
    # developing. If we provide a path such as /assets the CSP check fails.
    # See:
    #
    #   https://developer.chrome.com/extensions/contentSecurityPolicy#relaxing-remote-script
    if urlparse.urlparse(src).hostname not in ('localhost', '127.0.0.1'):
        src = urlparse.urljoin(src, request.webassets_env.url)

    value = {
        'src': src,
        'version': version,
        'version_name': version_name
    }

    return render('h:browser/chrome/manifest.json.jinja2', value,
                  request=request)


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


def settings_dict(env):
    """ Returns a dictionary of settings to be bundled with the extension """
    request = env['request']
    config = app_config(request)
    api_url = config['apiUrl']
    sentry_dsn = request.sentry.get_public_dsn('https')

    if sentry_dsn:
        config.update({
            'raven': {
              'dsn': sentry_dsn,
              'release': h.__version__,
            },
        })

    config.update({
        'buildType': build_type_from_api_url(api_url),
    })
    return config


def get_env(config_uri, base_url):
    """
    Return a preconfigured paste environment object. Sets up the WSGI
    application and ensures that webassets knows to load files from
    ``h:static`` regardless of the ``webassets.base_dir`` setting.
    """
    request = Request.blank('', base_url=base_url)
    env = paster.bootstrap(config_uri, request)
    request.root = env['root']

    request.sentry = raven.Client(release=raven.fetch_package_version('h'))

    # Ensure that the webassets URL is absolute
    request.webassets_env.url = urlparse.urljoin(base_url,
                                                 request.webassets_env.url)

    # Disable webassets caching and manifest generation
    request.webassets_env.cache = False
    request.webassets_env.manifest = False

    # By default, webassets will use its base_dir setting as its search path.
    # When building extensions, we change base_dir so as to build assets
    # directly into the extension directories. As a result, we have to add
    # back the correct search path.
    request.webassets_env.append_path(resolve('h:static').abspath(),
                                      request.webassets_env.url)

    return env


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
    paster.setup_logging(args.config_uri)

    os.environ['WEBASSETS_BASE_DIR'] = os.path.abspath('./build/chrome/public')
    if args.assets is not None:
        os.environ['WEBASSETS_BASE_URL'] = args.assets

    env = get_env(args.config_uri, args.base)

    # Prepare a fresh build.
    clean('build/chrome')
    os.makedirs('build/chrome')

    # Bundle the extension assets.
    webassets_env = env['request'].webassets_env
    content_dir = webassets_env.directory
    os.makedirs(content_dir)
    copytree('h/browser/chrome/content', 'build/chrome/content')
    copytree('h/browser/chrome/help', 'build/chrome/help')
    copytree('h/browser/chrome/images', 'build/chrome/images')
    copytree('h/static/images', 'build/chrome/public/images')

    os.makedirs('build/chrome/lib')

    subprocess_args = ['node_modules/.bin/browserify',
                       'h/browser/chrome/lib/extension.js',
                       '--outfile', 'build/chrome/lib/extension-bundle.js']
    if args.debug:
        subprocess_args.append('--debug')
    subprocess.call(subprocess_args)

    # Render the sidebar html.
    if webassets_env.url.startswith('chrome-extension:'):
        build_extension_common(env, bundle_app=True)
        request = env['request']
        context = {
          'app_config': app_config(request)
        }
        with codecs.open(content_dir + '/app.html', 'w', 'utf-8') as fp:
            data = render('h:templates/app.html.jinja2', context, request)
            fp.write(data)
    else:
        build_extension_common(env)

    # Render the manifest.
    with codecs.open('build/chrome/manifest.json', 'w', 'utf-8') as fp:
        data = chrome_manifest(env['request'])
        fp.write(data)

    # Write build settings to a JSON file
    with codecs.open('build/chrome/settings-data.js', 'w', 'utf-8') as fp:
        fp.write('window.EXTENSION_CONFIG = ' + json.dumps(settings_dict(env)))


parser = argparse.ArgumentParser('hypothesis-buildext')

parser.add_argument('config_uri',
                    help='paster configuration URI')

parser.add_argument('--debug', action='store_true', default=False,
                    help='create source maps to enable debugging in browser')

subparsers = parser.add_subparsers(title='browser', dest='browser')
subparsers.required = True

parser_chrome = subparsers.add_parser(
    'chrome',
    help="build the Google Chrome extension",
    description=textwrap.dedent(build_chrome.__doc__),
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser_chrome.add_argument('--base',
                           help='Base URL',
                           default='http://localhost:5000',
                           metavar='URL')
parser_chrome.add_argument('--assets',
                           help='A path (relative to base) or URL from which '
                                'to load the static assets',
                           default=None,
                           metavar='PATH/URL')


BROWSERS = {
    'chrome': build_chrome,
}


def main():
    # Set a flag in the environment that other code can use to detect if it's
    # running in a script rather than a full web application. See also
    # h/script.py.
    #
    # FIXME: This is a nasty hack and should go when we no longer need to spin
    # up an entire application to build the extensions.
    os.environ['H_SCRIPT'] = 'true'

    args = parser.parse_args()
    BROWSERS[args.browser](args)


if __name__ == '__main__':
    main()
