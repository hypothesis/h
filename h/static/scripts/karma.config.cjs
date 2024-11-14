/* global __dirname module require */

// eslint-disable-next-line @typescript-eslint/no-require-imports
const path = require('path');

module.exports = function (config) {
  config.set({
    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: './',

    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['mocha', 'source-map-support'],

    // list of files / patterns to load in the browser
    files: [
      // Test setup
      { pattern: '../../../build/scripts/tests.bundle.js', type: 'module' },

      // Sourcemaps for test bundles.
      { pattern: '../../../build/scripts/*.js.map', included: false },
    ],

    // list of files to exclude
    exclude: [],

    mochaReporter: {
      // Display a helpful diff when comparing complex objects
      // See https://www.npmjs.com/package/karma-mocha-reporter#showdiff
      showDiff: true,
      // Only show the total test counts and details for failed tests
      output: 'minimal',
    },

    coverageIstanbulReporter: {
      dir: path.join(__dirname, '../../../coverage'),
      reports: ['json', 'html'],
      'report-config': {
        json: { subdir: './' },
      },
      thresholds: {
        global: {
          statements: 100,
        },
      },
    },

    // Use https://www.npmjs.com/package/karma-mocha-reporter
    // for more helpful rendering of test failures
    reporters: ['progress', 'mocha', 'coverage-istanbul'],

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
    browsers: ['ChromeHeadless'],
    browserNoActivityTimeout: 20000, // Travis is slow...

    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false,

    // Log slow tests so we can fix them before they timeout
    reportSlowerThan: 500,
  });
};
