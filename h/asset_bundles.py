from webassets import Bundle
from pyramid_webassets import PyramidResolver

resolver = PyramidResolver()


def resolve_glob(path):
    # First argument is the context, we don't have one here.
    return resolver.search_for_source(None, path)


def process_path(path):
    if not isinstance(path, basestring):
        return path

    source = 'h:static/%s' % path

    # Process globs individually.
    if '*' in source:
        assets = (process_path(p) for p in resolve_glob(source))
        return Bundle(*assets)

    # Create a bundle per coffee file.
    if path.endswith('.coffee'):
        output = ('debug/%s' % path).replace('.coffee', '.js')
        return Bundle(path, filters='coffeescript', output=output)

    return source


def create_bundle(*assets):
    assets = (process_path(path) for path in assets)
    return Bundle(*assets)


app_dependencies_js = create_bundle(
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
    'scripts/plugin/threading.coffee')

app_js = create_bundle(
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
    'bootstrap.js')

app_css = Bundle(
    'h:static/scripts/vendor/katex/katex.min.css',
    Bundle('h:static/styles/icomoon.css',
           output='debug/styles/icomoon.css',
           filters='cssrewrite'),
    Bundle('h:static/styles/app.scss',
           filters='compass,cssrewrite',
           output='debug/styles/app.css',
           depends='h:static/styles/**/*.scss'))

inject_css = Bundle(
    'h:static/styles/inject.scss',
    filters='compass,cssrewrite',
    output='debug/styles/inject.css',
    depends='h:static/styles/**/*.scss')

topbar_css = Bundle(
    'h:static/styles/topbar.scss',
    filters='compass',
    output='debug/styles/topbar.css',
    depends='h:static/styles/**/*.scss')

inject_bundle = Bundle(
    'h:static/scripts/vendor/jquery.js',
    hypothesis_js, inject_css)

app_bundle = Bundle(
    'h:static/scripts/vendor/jquery.js',
    Bundle('h:static/scripts/vendor/angular.js',
           'h:static/scripts/vendor/angular-animate.js',
           'h:static/scripts/vendor/angular-route.js',
           'h:static/scripts/vendor/angular-sanitize.js',
           'h:static/scripts/vendor/ng-tags-input.js'),
    app_dependencies_js,
    helpers_js,
    account_js,
    session_js,
    app_js,
    app_css,
    topbar_css)


def register_bundles(config):
    config.add_webasset('inject', inject_bundle)
    config.add_webasset('app', app_bundle)
    config.add_webasset(
        'wgxpath',
        Bundle('h:static/scripts/vendor/polyfills/wgxpath.install.js'))
