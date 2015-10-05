// Karma configuration
var path = require('path');

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: './',

    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: [
      'browserify',
      'mocha',
      'chai',
      'sinon'
    ],

    // list of files / patterns to load in the browser
    files: [
      // Polyfills for PhantomJS
      './karma-phantomjs-polyfill.js',

      // Application external deps
      '../../../node_modules/jquery/dist/jquery.js',
      '../../../node_modules/angular/angular.js',
      '../../../node_modules/angular-animate/angular-animate.js',
      '../../../node_modules/angular-resource/angular-resource.js',
      '../../../node_modules/angular-route/angular-route.js',
      '../../../node_modules/angular-sanitize/angular-sanitize.js',
      '../../../node_modules/ng-tags-input/build/ng-tags-input.min.js',
      'vendor/angular-bootstrap-tabbable.js',
      'vendor/katex.js',

      // Test deps
      '../../../node_modules/angular-mocks/angular-mocks.js',
      '../../templates/client/*.html',
      'test/bootstrap.js',

      // Tests
      //
      // Karma watching is disabled for these files because they are
      // bundled with karma-browserify which handles watching itself via
      // watchify
      { pattern: '**/*-test.coffee', watched: false, included: true, served: true },
      { pattern: '**/*-test.js', watched: false, included: true, served: true }
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
      './karma-phantomjs-polyfill.js': ['browserify'],
      '**/*-test.js': ['browserify'],
      '**/*-test.coffee': ['browserify'],
      '../../templates/client/*.html': ['ng-html2js'],
    },

    browserify: {
      debug: true,
      extensions: ['.coffee'],
      configure: function (bundle) {
        bundle
          .transform('coffeeify')
          .plugin('proxyquire-universal')
          .require('phantom-ownpropertynames/implement', {entry: true});
      }
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

    // warn about tests that take a long time to execute,
    // in combination with per-test timeouts this can also be used
    // to discover whether tests that intermittently timeout are merely slow,
    // in which case they will trigger a warning,
    // or failing to complete at all within the extended timeout
    reportSlowerThan: 500,

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
