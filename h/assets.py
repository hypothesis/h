# -*- coding: utf-8 -*-
import os

import json
from pyramid.httpexceptions import HTTPNotFound
from pyramid.settings import aslist
from pyramid.static import static_view

from h._compat import configparser


class _CachedFile(object):

    """
    Parses content from a file and caches the result until the file changes.

    _CachedFile reads a file at a given path and parses the content using a
    provided loader. The result is cached until the mtime of the file changes.
    """

    def __init__(self, path, loader):
        """
        :param path: The path to the file to load.
        :param loader: A callable that will be passed the file object and
                       should return the parsed content.
        """
        self.path = path
        self.loader = loader
        self._mtime = None
        self._cached = None

    def load(self):
        """
        Return the current content of the file parsed with the loader.

        If the file has not been loaded or has changed since the last call
        to load(), it will be reloaded, otherwise the cached content will
        be returned.
        """
        current_mtime = os.path.getmtime(self.path)
        if not self._mtime or self._mtime < current_mtime:
            self._cached = self.loader(open(self.path))
            self._mtime = current_mtime
        return self._cached


class Environment(object):

    """
    Environment for generating URLs for Hypothesis' static assets.

    Static assets are grouped into named bundles, defined in an ini-format
    config file. The relative URL that should be used when serving a file from
    a bundle is defined in a JSON manifest file, which is generated by the
    static asset build pipeline.

    Environment reads the set of bundles from the config file
    and the mapping between the file path and the output URL
    from a JSON manifest file and provides the ability to retrieve the final
    URLs for a bundle via the urls() method.
    """

    def __init__(self, assets_base_url, bundle_config_path, manifest_path):
        """
        Construct an Environment from the given configuration files.

        :param assets_base_url: The URL at which assets will be served,
                                excluding the trailing slash.
        :param bundle_config_path: Asset bundles config file.
        :param manifest_path: JSON file mapping file paths in the bundle config
                              file to cache-busted URLs.
        """
        self.assets_base_url = assets_base_url
        self.manifest = _CachedFile(manifest_path, json.load)
        self.bundles = _CachedFile(bundle_config_path, _load_bundles)

    def files(self, bundle):
        """Return the file paths for all files in a bundle."""
        bundles = self.bundles.load()
        return bundles[bundle]

    def urls(self, bundle):
        """
        Return asset URLs for all files in a bundle.

        Returns the URLs at which all files in a bundle are served,
        read from the asset manifest.
        """
        manifest = self.manifest.load()
        bundles = self.bundles.load()

        def asset_url(path):
            return '{}/{}'.format(self.assets_base_url, manifest[path])
        return [asset_url(path) for path in bundles[bundle]]

    def version(self, path):
        """
        Return the current version of the asset with a given `path`.

        Returns `None` if no such asset exists.
        """
        try:
            # Asset URLs in the bundle are in the form '<path>?<version>'
            manifest = self.manifest.load()
            [_, version] = manifest[path].split('?')
            return version
        except KeyError:
            return None


def _check_version(env, wrapped):
    """
    View callable decorator which checks the requested version of a static asset.

    This checks the asset version specified in the query string against the
    available version specified in the JSON manifest. If the two versions do not
    match, the request is failed with a 404 response.
    """
    def wrapper(context, request):
        requested_version = request.query_string

        if requested_version:
            asset_path = request.path[len(env.assets_base_url)+1:]
            expected_version = env.version(asset_path)

            if requested_version != expected_version:
                return HTTPNotFound('Asset version not available.')

        return wrapped(context, request)

    return wrapper


def _add_cors_header(wrapped):
    """
    View callable decorator which adds CORS headers to the request.
    """
    def wrapper(context, request):
        # Add a CORS header to the response because static assets from
        # the sidebar are loaded into pages served by a different origin:
        # The domain hosting the page into which the sidebar has been injected
        # or embedded.
        #
        # Some browsers enforce cross-origin restrictions on certain types of
        # resources, eg. Firefox enforces same-domain policy for @font-face
        # unless a CORS header is provided.
        response = wrapped(context, request)
        response.headers.extend({
            'Access-Control-Allow-Origin': '*'
        })
        return response

    return wrapper


def _load_bundles(fp):
    """Read an asset bundle config from a file object."""
    parser = configparser.ConfigParser()
    parser.readfp(fp)
    return {k: aslist(v) for k, v in parser.items('bundles')}


ABOUT_TEN_YEARS = 60 * 60 * 24 * 365 * 10


def create_assets_view(assets_env, file_path):
    """
    Create an `Environment` and view callable for serving static assets.

    :param env: The `Environment`
    :param file_path: Package or file path of directory containing assets
    :rtype: (Environment, callable)
    """
    assets_view = static_view(file_path,
                              cache_max_age=ABOUT_TEN_YEARS,
                              use_subpath=True)
    assets_view = _check_version(assets_env, assets_view)
    assets_view = _add_cors_header(assets_view)
    return assets_view


def includeme(config):
    # Site assets
    assets_env = Environment('/assets',
                             'h/assets.ini',
                             'build/manifest.json')
    assets_view = create_assets_view(assets_env, 'h:../build')

    # Client assets
    assets_client_env = Environment('/assets/client',
                                    'h/assets_client.ini',
                                    'node_modules/hypothesis/build/manifest.json')
    assets_client_view = create_assets_view(assets_client_env,
                                            'h:../node_modules/hypothesis/build')

    config.add_view(route_name='assets', view=assets_view)
    config.add_view(route_name='assets_client', view=assets_client_view)

    # We store the environment objects on the registry so that the Jinja2
    # integration can be configured in app.py
    config.registry['assets_env'] = assets_env
    config.registry['assets_client_env'] = assets_client_env
