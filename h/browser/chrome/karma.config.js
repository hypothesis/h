'use strict';

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
      '../../static/scripts/karma-phantomjs-polyfill.js',

      {
        pattern: 'test/settings.json',
        included: false,
      },

      './lib/polyfills.js',
      './test/bootstrap.js',
      './test/*.js',
    ],

    // list of files to exclude
    exclude: [
    ],

    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
      '../../static/scripts/karma-phantomjs-polyfill.js': ['browserify'],
      './lib/*.js': ['browserify'],
      './test/*.js': ['browserify'],
    },

    browserify: {
      debug: true,
      configure: function(bundle) {
        bundle
          .plugin('proxyquire-universal')
          // fix for Proxyquire in PhantomJS 1.x.
          // See https://github.com/bitwit/proxyquireify-phantom-menace
          .require(require.resolve('phantom-ownpropertynames/implement'),
            {entry: true});
      },
    },

    mochaReporter: {
      // Display a helpful diff when comparing complex objects
      // See https://www.npmjs.com/package/karma-mocha-reporter#showdiff
      showDiff: true,
      // Only show the total test counts and details for failed tests
      output: 'minimal',
    },

    // Use https://www.npmjs.com/package/karma-mocha-reporter
    // for more helpful rendering of test failures
    reporters: ['mocha'],


    // web server port
    port: 9877,


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


    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false
  });
};
