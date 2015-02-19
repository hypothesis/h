// Karma configuration
// Generated on Mon Jul 14 2014 14:06:50 GMT+0200 (CEST)

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['mocha'],


    // list of files / patterns to load in the browser
    files: [
      'h/static/scripts/vendor/polyfills/bind.js',
      'h/static/scripts/vendor/polyfills/url.js',
      'h/static/scripts/vendor/polyfills/promise.js',
      'h/static/scripts/vendor/jquery.js',
      'h/static/scripts/vendor/jschannel.js',
      'h/static/scripts/vendor/jwz.js',
      'h/static/scripts/vendor/moment-with-langs.js',
      'h/static/scripts/vendor/jstz.js',
      'h/static/scripts/vendor/moment-timezone.js',
      'h/static/scripts/vendor/moment-timezone-data.js',
      'h/static/scripts/vendor/Markdown.Converter.js',
      'h/static/scripts/vendor/unorm.js',
      'h/static/scripts/vendor/uuid.js',
      'h/static/scripts/vendor/annotator.js',
      'h/static/scripts/annotator/monkey.js',
      'h/static/scripts/vendor/annotator.auth.js',
      'h/static/scripts/annotator/plugin/bridge.js',
      'h/static/scripts/annotator/plugin/bucket-bar.js',
      'h/static/scripts/vendor/dom_text_mapper.js',
      'h/static/scripts/annotator/annotator.anchoring.js',
      // Angular needs to be included after annotator to avoid the
      // CrossFrame dependencies in Bridge picking up the angular object.
      'h/static/scripts/vendor/angular.js',
      'h/static/scripts/vendor/angular-mocks.js',
      'h/static/scripts/vendor/angular-animate.js',
      'h/static/scripts/vendor/angular-bootstrap.js',
      'h/static/scripts/vendor/angular-recursion.js',
      'h/static/scripts/vendor/angular-resource.js',
      'h/static/scripts/vendor/angular-route.js',
      'h/static/scripts/vendor/angular-sanitize.js',
      'h/static/scripts/vendor/ng-tags-input.js',
      'h/static/scripts/annotator/plugin/texthighlights.js',
      'h/static/scripts/app.js',
      'h/static/scripts/account.js',
      'h/static/scripts/helpers.js',
      'h/static/scripts/session.js',
      'h/static/scripts/hypothesis.js',
      'h/static/scripts/vendor/sinon.js',
      'h/static/scripts/vendor/chai.js',
      'h/templates/client/*.html',
      'tests/js/bootstrap.coffee',
      'tests/js/**/*-test.coffee'
    ],


    // list of files to exclude
    exclude: [
    ],

    // strip templates of leading path
    ngHtml2JsPreprocessor: {
      moduleName: 'h.templates',
      stripPrefix: 'h/templates/client/'
    },

    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
      '**/*.coffee': ['coffee'],
      'h/templates/client/*.html': ['ng-html2js'],
    },


    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['dots'],


    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: false,


    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['PhantomJS'],


    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false,
  });
};
