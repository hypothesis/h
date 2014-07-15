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
      'h/lib/jquery-1.10.2.js',
      'h/lib/jquery.mousewheel.js',
      'h/lib/angular.js',
      'h/lib/angular-mocks.js',
      'h/lib/angular-animate.js',
      'h/lib/angular-bootstrap.js',
      'h/lib/angular-resource.js',
      'h/lib/angular-route.js',
      'h/lib/angular-sanitize.js',
      'h/lib/gettext.js',
      'h/locale/data.js',
      'h/lib/annotator.js',
      'h/lib/annotator.auth.js',
      'h/js/plugin/bridge.js',
      'h/js/plugin/discovery.js',
      'h/lib/annotator.document.js',
      'h/lib/annotator.permissions.js',
      'h/lib/annotator.store.js',
      'h/js/plugin/threading.js',
      'h/lib/jschannel.js',
      'h/lib/jwz.js',
      'h/lib/moment-with-langs.js',
      'h/lib/jstz.js',
      'h/lib/moment-timezone.js',
      'h/lib/moment-timezone-data.js',
      'h/lib/Markdown.Converter.js',
      'h/lib/polyfills/raf.js',
      'h/lib/sockjs-0.3.4.js',
      'h/lib/jquery.ui.core.js',
      'h/lib/jquery.ui.position.js',
      'h/lib/jquery.ui.widget.js',
      'h/lib/jquery.ui.tooltip.js',
      'h/lib/jquery.ui.autocomplete.js',
      'h/lib/jquery.ui.menu.js',
      'h/lib/jquery.ui.effect.js',
      'h/lib/jquery.ui.effect-blind.js',
      'h/lib/jquery.ui.effect-forecolor-highlight.js',
      'h/lib/jquery.ui.effect-highlight.js',
      'h/lib/tag-it.js',
      'h/lib/uuid.js',
      'h/lib/underscore-1.4.3.js',
      'h/lib/backbone-0.9.10.js',
      'h/lib/visualsearch.js',
      'h/js/hypothesis.js',
      'h/lib/sinon.js',
      'h/lib/chai.js',
      'tests/js/**/*-test.coffee'
    ],


    // list of files to exclude
    exclude: [
    ],


    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
      '**/*.coffee': ['coffee']
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
    singleRun: false
  });
};
