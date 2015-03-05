// Karma configuration
// Generated on Mon Jul 14 2014 14:06:50 GMT+0200 (CEST)

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: [
      'browserify',
      'mocha'
    ],


    // list of files / patterns to load in the browser
    files: [
      // Application external deps
      'h/static/scripts/vendor/jquery.js',
      'h/static/scripts/vendor/angular.js',
      'h/static/scripts/vendor/angular-animate.js',
      'h/static/scripts/vendor/angular-bootstrap.js',
      'h/static/scripts/vendor/angular-resource.js',
      'h/static/scripts/vendor/angular-route.js',
      'h/static/scripts/vendor/angular-sanitize.js',
      'h/static/scripts/vendor/ng-tags-input.js',
      'h/static/scripts/vendor/annotator.js',
      'h/static/scripts/vendor/polyfills/autofill-event.js',
      'h/static/scripts/vendor/polyfills/bind.js',
      'h/static/scripts/vendor/katex/katex.js',
      'h/static/scripts/vendor/moment-with-langs.js',
      'h/static/scripts/vendor/jstz.js',
      'h/static/scripts/vendor/moment-timezone.js',
      'h/static/scripts/vendor/moment-timezone-data.js',
      'h/static/scripts/vendor/polyfills/url.js',

      // Test deps
      'h/static/scripts/vendor/angular-mocks.js',
      'h/static/scripts/vendor/polyfills/promise.js',
      'h/static/scripts/vendor/sinon.js',
      'h/static/scripts/vendor/chai.js',
      'h/templates/client/*.html',
      'h/static/scripts/test/bootstrap.coffee',

      // Tests
      'h/static/scripts/**/*-test.coffee'
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
      '**/*.coffee': ['browserify'],
      'h/templates/client/*.html': ['ng-html2js'],
    },

    browserify: {
      debug: true,
      extensions: ['.coffee']
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
    autoWatch: true,


    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['PhantomJS'],
    browserNoActivityTimeout: 20000, // Travis is slow...

    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false,
  });
};
