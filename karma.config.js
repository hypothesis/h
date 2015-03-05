// Karma configuration
// Generated on Mon Jul 14 2014 14:06:50 GMT+0200 (CEST)
var path = require('path');

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: 'h/static/scripts',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: [
      'browserify',
      'mocha'
    ],


    // list of files / patterns to load in the browser
    files: [
      // Application external deps
      'vendor/jquery.js',
      'vendor/angular.js',
      'vendor/angular-animate.js',
      'vendor/angular-bootstrap.js',
      'vendor/angular-resource.js',
      'vendor/angular-route.js',
      'vendor/angular-sanitize.js',
      'vendor/ng-tags-input.js',
      'vendor/annotator.js',
      'vendor/polyfills/autofill-event.js',
      'vendor/polyfills/bind.js',
      'vendor/katex/katex.js',
      'vendor/moment-with-langs.js',
      'vendor/jstz.js',
      'vendor/moment-timezone.js',
      'vendor/moment-timezone-data.js',
      'vendor/polyfills/url.js',

      // Test deps
      'vendor/angular-mocks.js',
      'vendor/polyfills/promise.js',
      'vendor/sinon.js',
      'vendor/chai.js',
      '../../templates/client/*.html',
      'test/bootstrap.coffee',

      // Tests
      '**/*-test.coffee'
    ],


    // list of files to exclude
    exclude: [
    ],

    // strip templates of leading path
    ngHtml2JsPreprocessor: {
      moduleName: 'h.templates',
      cacheIdFromPath: path.basename
    },

    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
      '**/*.coffee': ['browserify'],
      '../../templates/client/*.html': ['ng-html2js'],
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
