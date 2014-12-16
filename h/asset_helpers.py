"""
Helpers for building webassets bundles. This simplifies the amount of
boilerplate required for bundles by making certain assumptions about
filenames. For example files ending in coffee will be processed with
a coffee filter, likewise with scss files.
"""
from webassets import Bundle
from pyramid_webassets import PyramidResolver

RESOLVER = PyramidResolver()

# First argument is the context, we don't have one here.
PKG_PREFIX = 'h:static/'
STATIC_ROOT = RESOLVER.search_for_source(None, PKG_PREFIX)


def create_bundle(*assets):
    """ Creates a new Bundle """
    assets = (_process_path(path) for path in assets)
    return Bundle(*assets)


def _process_path(path):
    """ Processes a single asset path and returns a Bundle """
    if not isinstance(path, basestring):
        return path

    source = PKG_PREFIX + path

    # Process globs individually.
    if '*' in source:
        return _build_glob_bundle(source)

    # Create a bundle per coffee file.
    if path.endswith('.coffee'):
        return _build_coffee_bundle(source, path)

    if path.endswith('.scss'):
        return _build_scss_bundle(source, path)

    return source


def _build_coffee_bundle(source, original_path):
    """ Creates a bundle for a single CoffeeScript file """
    output = ('debug/%s' % original_path).replace('.coffee', '.js')
    return Bundle(source, filters='coffeescript', output=output)


def _build_scss_bundle(source, original_path):
    """ Creates a bundle for a single SCSS file """
    output = ('debug/%s' % original_path).replace('.scss', '.css')
    return Bundle(source, filters='compass,cssrewrite', output=output,
                  depends='h:static/styles/**/*.scss')


def _build_glob_bundle(source):
    """ Parses a glob path and returns a bundle containing each match """
    assets = (_process_path(p) for p in _resolve_glob(source))
    return Bundle(*assets)


def _resolve_glob(source):
    """ Resolves an asset source (with a package namespace) containing a
        glob character. This will then return a basic path without the
        namespace so that it can be passed to _process_path. """
    matches = RESOLVER.search_for_source(None, source)
    return (p.replace(STATIC_ROOT, '') for p in matches)
