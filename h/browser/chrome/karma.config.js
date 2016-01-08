// Karma configuration
// Generated on Mon Nov 17 2014 13:59:51 GMT+0000 (GMT)

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
      './test/*.js',
    ],

    proxies: {
      "/settings.json": "/base/test/settings.json"
    },

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
          .require('phantom-ownpropertynames/implement', {entry: true});
      },
    },

    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['dots'],


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
