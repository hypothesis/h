from webassets import Bundle

app_dependencies_js = Bundle(
    'h:static/scripts/vendor/jschannel.js',
    'h:static/scripts/vendor/jwz.js',
    'h:static/scripts/vendor/moment-with-langs.js',
    'h:static/scripts/vendor/jstz.js',
    'h:static/scripts/vendor/moment-timezone.js',
    'h:static/scripts/vendor/moment-timezone-data.js',
    'h:static/scripts/vendor/Markdown.Converter.js',
    'h:static/scripts/vendor/polyfills/autofill-event.js',
    'h:static/scripts/vendor/unorm.js',
    'h:static/scripts/vendor/uuid.js',
    'h:static/scripts/vendor/gettext.js',
    'h:static/scripts/vendor/katex/katex.js',
    'h:static/scripts/vendor/annotator.js',
    'h:static/scripts/vendor/annotator.auth.js',
    'h:static/scripts/vendor/annotator.document.js',
    'h:static/scripts/vendor/annotator.permissions.js',
    'h:static/scripts/vendor/annotator.store.js',
    Bundle('h:static/scripts/plugin/bridge.coffee',
           filters='coffeescript',
           output='debug/scripts/plugin/bridge.js'),
    Bundle('h:static/scripts/plugin/discovery.coffee',
           filters='coffeescript',
           output='debug/scripts/plugin/discovery.js'),
    Bundle('h:static/scripts/plugin/threading.coffee',
           filters='coffeescript',
           output='debug/scripts/plugin/threading.js'))

app_js = Bundle(
    'h:static/scripts/app.coffee',
    'h:static/scripts/controllers.coffee',
    'h:static/scripts/directives.coffee',
    'h:static/scripts/directives/*.coffee',
    'h:static/scripts/filters.coffee',
    'h:static/scripts/searchfilters.coffee',
    'h:static/scripts/services.coffee',
    'h:static/scripts/*-service.coffee',
    'h:static/scripts/streamsearch.coffee',
    filters='coffeescript',
    output='debug/scripts/app.js')

account_js = Bundle(
    'h:static/scripts/account/account.coffee',
    'h:static/scripts/account/*-controller.coffee',
    'h:static/scripts/account/*-service.coffee',
    output='scripts/account.js',
    filters='coffeescript')

helpers_js = Bundle(
    'h:static/scripts/vendor/angular-bootstrap.js',
    Bundle('h:static/scripts/helpers/helpers.coffee',
           'h:static/scripts/helpers/*-helpers.coffee',
           filters='coffeescript',
           output='debug/scripts/helpers.js'))

session_js = Bundle(
    'h:static/scripts/vendor/angular-resource.js',
    Bundle('h:static/scripts/session/session.coffee',
           'h:static/scripts/session/*-service.coffee',
           filters='coffeescript',
           output='debug/scripts/session.js')
)

hypothesis_js = Bundle(
    'h:static/scripts/vendor/jquery.scrollintoview.js',
    'h:static/scripts/vendor/jschannel.js',
    'h:static/scripts/vendor/gettext.js',
    'h:static/scripts/vendor/annotator.js',
    'h:static/scripts/vendor/annotator.document.js',
    'h:static/scripts/vendor/diff_match_patch_uncompressed.js',
    'h:static/scripts/vendor/dom_text_mapper.js',
    'h:static/scripts/vendor/dom_text_matcher.js',
    'h:static/scripts/vendor/text_match_engines.js',
    'h:static/scripts/vendor/annotator.domtextmapper.js',
    'h:static/scripts/vendor/annotator.textanchors.js',
    'h:static/scripts/vendor/annotator.fuzzytextanchors.js',
    'h:static/scripts/vendor/page_text_mapper_core.js',
    'h:static/scripts/vendor/annotator.pdf.js',
    'h:static/scripts/vendor/annotator.textanchors.js',
    'h:static/scripts/vendor/annotator.textrange.js',
    'h:static/scripts/vendor/annotator.textposition.js',
    'h:static/scripts/vendor/annotator.textquote.js',
    'h:static/scripts/vendor/annotator.texthighlights.js',
    Bundle('h:static/scripts/plugin/bridge.coffee',
           filters='coffeescript',
           output='debug/scripts/plugin/bridge.js'),
    Bundle('h:static/scripts/plugin/bucket-bar.coffee',
           filters='coffeescript',
           output='debug/scripts/plugin/bucket-bar.js'),
    Bundle('h:static/scripts/plugin/toolbar.coffee',
           filters='coffeescript',
           output='debug/scripts/plugin/toolbar.js'),
    Bundle('h:static/scripts/guest.coffee',
           'h:static/scripts/host.coffee',
           filters='coffeescript',
           output='debug/scripts/hypothesis.js'),
    'h:static/bootstrap.js')

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
