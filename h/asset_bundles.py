from os import path
from pyramid.settings import asbool
from .asset_helpers import create_bundle

app_js = create_bundle(
    'scripts/vendor/jschannel.js',
    'scripts/vendor/jwz.js',
    'scripts/vendor/moment-with-langs.js',
    'scripts/vendor/jstz.js',
    'scripts/vendor/moment-timezone.js',
    'scripts/vendor/moment-timezone-data.js',
    'scripts/vendor/Markdown.Converter.js',
    'scripts/vendor/polyfills/autofill-event.js',
    'scripts/vendor/unorm.js',
    'scripts/vendor/uuid.js',
    'scripts/vendor/gettext.js',
    'scripts/vendor/katex/katex.js',
    'scripts/vendor/annotator.js',
    'scripts/vendor/annotator.auth.js',
    'scripts/vendor/annotator.document.js',
    'scripts/vendor/annotator.permissions.js',
    'scripts/vendor/annotator.store.js',
    'scripts/plugin/bridge.coffee',
    'scripts/plugin/discovery.coffee',
    'scripts/plugin/threading.coffee',
    'scripts/app.coffee',
    'scripts/controllers.coffee',
    'scripts/directives.coffee',
    'scripts/directives/*.coffee',
    'scripts/filters.coffee',
    'scripts/searchfilters.coffee',
    'scripts/services.coffee',
    'scripts/*-service.coffee',
    'scripts/streamsearch.coffee')

account_js = create_bundle(
    'scripts/account/account.coffee',
    'scripts/account/*-controller.coffee',
    'scripts/account/*-service.coffee')

helpers_js = create_bundle(
    'scripts/vendor/angular-bootstrap.js',
    'scripts/helpers/helpers.coffee',
    'scripts/helpers/*-helpers.coffee')

session_js = create_bundle(
    'scripts/vendor/angular-resource.js',
    'scripts/session/session.coffee',
    'scripts/session/*-service.coffee')

hypothesis_js = create_bundle(
    'scripts/vendor/jquery.scrollintoview.js',
    'scripts/vendor/jschannel.js',
    'scripts/vendor/gettext.js',
    'scripts/vendor/annotator.js',
    'scripts/vendor/annotator.document.js',
    'scripts/vendor/diff_match_patch_uncompressed.js',
    'scripts/vendor/dom_text_mapper.js',
    'scripts/vendor/dom_text_matcher.js',
    'scripts/vendor/text_match_engines.js',
    'scripts/vendor/annotator.domtextmapper.js',
    'scripts/vendor/annotator.textanchors.js',
    'scripts/vendor/annotator.fuzzytextanchors.js',
    'scripts/vendor/page_text_mapper_core.js',
    'scripts/vendor/annotator.pdf.js',
    'scripts/vendor/annotator.textanchors.js',
    'scripts/vendor/annotator.textrange.js',
    'scripts/vendor/annotator.textposition.js',
    'scripts/vendor/annotator.textquote.js',
    'scripts/vendor/annotator.texthighlights.js',
    'scripts/plugin/bridge.coffee',
    'scripts/plugin/bucket-bar.coffee',
    'scripts/plugin/toolbar.coffee',
    'scripts/guest.coffee',
    'scripts/host.coffee',
    'scripts/bootstrap.js')

app_css = create_bundle(
    'scripts/vendor/katex/katex.min.css',
    'styles/icomoon.css',
    'styles/app.scss')

hypothesis_css = create_bundle(
    'styles/inject.scss')


def register_bundles(config):
    """ Registers the bundles with the application """

    def output_bundle(*bundles, **kwargs):
        """
        Helper class to apply the correct filters and filename to each bundle
        depending on whether they should be minified or not. This should
        be called with a series of bundle instances and an output filepath.
        """
        output = kwargs['output']
        filters = None

        if asbool(config.registry.settings['hassets.minify']):
            filename, ext = path.splitext(output)
            output = '%s.min%s' % (filename, ext)
            if ext.endswith('.css'):
                filters = 'cleancss'
            elif ext.endswith('.js'):
                filters = 'uglifyjs'

        return create_bundle(*bundles, output=output, filters=filters)

    # Define output files for dependencies.
    topbar_bundle = output_bundle(
        'styles/topbar.scss',
        output='build/styles/topbar.css')

    jquery_bundle = output_bundle(
        'scripts/vendor/jquery.js',
        output='build/scripts/vendor/jquery.js')

    angular_bundle = output_bundle(
        'scripts/vendor/angular.js',
        'scripts/vendor/angular-animate.js',
        'scripts/vendor/angular-route.js',
        'scripts/vendor/angular-sanitize.js',
        'scripts/vendor/ng-tags-input.js',
        output='build/scripts/vendor/angular.js')

    inject_bundle = create_bundle(
        jquery_bundle,
        output_bundle(
            hypothesis_js,
            output='build/scripts/hypothesis.js'),
        output_bundle(
            hypothesis_css,
            output='build/styles/hypothesis.css'))

    app_bundle = create_bundle(
        jquery_bundle,
        angular_bundle,
        output_bundle(
            app_js,
            output='build/scripts/app.js'),
        output_bundle(
            helpers_js,
            output='build/scripts/helpers.js'),
        output_bundle(
            account_js,
            output='build/scripts/account.js'),
        output_bundle(
            session_js,
            output='build/scripts/session.js'),
        output_bundle(
            app_css,
            output='build/styles/app.css'))

    wgxpath_bundle = output_bundle(
        'scripts/vendor/polyfills/wgxpath.install.js',
        output='build/scripts/vendor/polyfills/wgxpath')

    # Register the bundles with the application.
    config.add_webasset('inject', inject_bundle)
    config.add_webasset('app', app_bundle)
    config.add_webasset('topbar', topbar_bundle)
    config.add_webasset('wgxpath', wgxpath_bundle)
