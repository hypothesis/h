'use strict';

require('core-js/es6/promise');
require('core-js/fn/object/assign');
require('core-js/fn/string');

var path = require('path');

var batch = require('gulp-batch');
var changed = require('gulp-changed');
var commander = require('commander');
var endOfStream = require('end-of-stream');
var gulp = require('gulp');
var gulpIf = require('gulp-if');
var gulpUtil = require('gulp-util');
var newer = require('gulp-newer');
var postcss = require('gulp-postcss');
var postcssURL = require('postcss-url');
var svgmin = require('gulp-svgmin');
var through = require('through2');

var createBundle = require('./scripts/gulp/create-bundle');
var createStyleBundle = require('./scripts/gulp/create-style-bundle');
var manifest = require('./scripts/gulp/manifest');

var IS_PRODUCTION_BUILD = process.env.NODE_ENV === 'production';
var SCRIPT_DIR = 'build/scripts';
var STYLE_DIR = 'build/styles';
var FONTS_DIR = 'build/fonts';
var IMAGES_DIR = 'build/images';

function parseCommandLine() {
  commander
    // Test configuration.
    // See https://github.com/karma-runner/karma-mocha#configuration
    .option('--grep [pattern]', 'Run only tests matching a given pattern')
    .parse(process.argv);

  if (commander.grep) {
    gulpUtil.log(`Running tests matching pattern /${commander.grep}/`);
  }

  return {
    grep: commander.grep,
  };
}

var taskArgs = parseCommandLine();

function getEnv(key) {
  if (!process.env.hasOwnProperty(key)) {
    throw new Error(`Environment variable ${key} is not set`);
  }
  return process.env[key];
}

var vendorBundles = {
  jquery: ['jquery'],
  bootstrap: ['bootstrap'],
  raven: ['raven-js'],
  unorm: ['unorm'],
};
var vendorModules = ['jquery', 'bootstrap', 'raven-js', 'unorm'];
var vendorNoParseModules = ['jquery', 'unorm'];

// Builds the bundles containing vendor JS code
gulp.task('build-vendor-js', function () {
  var finished = [];
  Object.keys(vendorBundles).forEach(function (name) {
    finished.push(createBundle({
      name: name,
      require: vendorBundles[name],
      minify: IS_PRODUCTION_BUILD,
      path: SCRIPT_DIR,
      noParse: vendorNoParseModules,
    }));
  });
  return Promise.all(finished);
});

var bundleBaseConfig = {
  path: SCRIPT_DIR,
  external: vendorModules,
  minify: IS_PRODUCTION_BUILD,
  noParse: vendorNoParseModules,
};

var bundles = [{
  // Public-facing website
  name: 'site',
  entry: './h/static/scripts/site',
},{
  // Admin areas of the site
  name: 'admin-site',
  entry: './h/static/scripts/admin-site',
},{
  // Legacy site bundle (for old homepage)
  name: 'legacy-site',
  entry: './h/static/scripts/legacy-site',
},{
  // Header script inserted inline at the top of the page
  name: 'header',
  entry: './h/static/scripts/header',
},{
  // Helper script for the OAuth post-authorization page.
  name: 'post-auth',
  entry: './h/static/scripts/post-auth',
}];

var bundleConfigs = bundles.map(function (config) {
  return Object.assign({}, bundleBaseConfig, config);
});

gulp.task('build-js', ['build-vendor-js'], function () {
  return Promise.all(bundleConfigs.map(function (config) {
    return createBundle(config);
  }));
});

gulp.task('watch-js', ['build-vendor-js'], function () {
  bundleConfigs.map(function (config) {
    createBundle(config, {watch: true});
  });
});

// Rewrite font URLs to look for fonts in 'build/fonts' instead of
// 'build/styles/fonts'
function rewriteCSSURL(url) {
  return url.replace(/^fonts\//, '../fonts/');
}

gulp.task('build-vendor-css', function () {
  var vendorCSSFiles = [
    // `front-page.css` is a pre-built bundle of legacy CSS used by the home
    // page
    './h/static/styles/front-page.css',

    // `legacy-site.css` is a pre-built bundle of legacy CSS used by the
    // login and account settings pages
    './h/static/styles/legacy-site.css',

    // Icon font
    './h/static/styles/vendor/icomoon.css',
    './node_modules/bootstrap/dist/css/bootstrap.css',
  ];

  var cssURLRewriter = postcssURL({
    url: rewriteCSSURL,
  });

  return gulp.src(vendorCSSFiles)
    .pipe(newer(STYLE_DIR))
    .pipe(postcss([cssURLRewriter]))
    .pipe(gulp.dest(STYLE_DIR));
});

var styleBundleEntryFiles = [
  './h/static/styles/admin.scss',
  './h/static/styles/help-page.scss',
  './h/static/styles/site.scss',
  './h/static/styles/old-home.scss',
];

function buildStyleBundle(entryFile, options) {
  return createStyleBundle({
    input: entryFile,
    output: './build/styles/' + path.basename(entryFile, '.scss') + '.css',
    minify: IS_PRODUCTION_BUILD,
    urlRewriter: rewriteCSSURL,
    watch: options.watch,
  });
}

gulp.task('build-css', ['build-vendor-css'], function () {
  return Promise.all(styleBundleEntryFiles.map(buildStyleBundle));
});

gulp.task('watch-css', function () {
  // Build initial CSS bundles. This is done rather than adding 'build-css' as
  // a dependency of this task so that the process continues in the event of an
  // error.
  Promise.all(styleBundleEntryFiles.map(buildStyleBundle)).catch(gulpUtil.log);
  gulp.watch('h/static/styles/**/*.scss', ['build-css']);
});

var fontFiles = 'h/static/styles/vendor/fonts/*.woff';

gulp.task('build-fonts', function () {
  gulp.src(fontFiles)
    .pipe(changed(FONTS_DIR))
    .pipe(gulp.dest(FONTS_DIR));
});

gulp.task('watch-fonts', function () {
  gulp.watch(fontFiles, ['build-fonts']);
});

var imageFiles = 'h/static/images/**/*';
gulp.task('build-images', function () {
  var shouldMinifySVG = function (file) {
    return IS_PRODUCTION_BUILD && file.path.match(/\.svg$/);
  };

  gulp.src(imageFiles)
    .pipe(changed(IMAGES_DIR))
    .pipe(gulpIf(shouldMinifySVG, svgmin()))
    .pipe(gulp.dest(IMAGES_DIR));
});

gulp.task('watch-images', function () {
  gulp.watch(imageFiles, ['build-images']);
});

var MANIFEST_SOURCE_FILES = 'build/@(fonts|images|scripts|styles)/**/*.*';

/**
 * Generate a JSON manifest mapping file paths to
 * URLs containing cache-busting query string parameters.
 */
function generateManifest() {
  gulp.src(MANIFEST_SOURCE_FILES)
    .pipe(manifest({name: 'manifest.json'}))
    .pipe(through.obj(function (file, enc, callback) {
      gulpUtil.log('Updated asset manifest');
      this.push(file);
      callback();
    }))
    .pipe(gulp.dest('build/'));
}

gulp.task('watch-manifest', function () {
  gulp.watch(MANIFEST_SOURCE_FILES, batch(function (events, done) {
    endOfStream(generateManifest(), function () {
      done();
    });
  }));
});

gulp.task('build',
          ['build-js',
           'build-css',
           'build-fonts',
           'build-images'],
          generateManifest);

gulp.task('watch',
          ['watch-js',
           'watch-css',
           'watch-fonts',
           'watch-images',
           'watch-manifest']);

function runKarma(baseConfig, opts, done) {
  // See https://github.com/karma-runner/karma-mocha#configuration
  var cliOpts = {
    client: {
      mocha: {
        grep: taskArgs.grep,
      },
    },
  };

  // Work around a bug in Karma 1.10 which causes console log messages not to
  // be displayed when using a non-default reporter.
  // See https://github.com/karma-runner/karma/pull/2220
  var BaseReporter = require('karma/lib/reporters/base');
  BaseReporter.decoratorFactory.$inject =
    BaseReporter.decoratorFactory.$inject.map(dep =>
        dep.replace('browserLogOptions', 'browserConsoleLogOptions'));

  var karma = require('karma');
  new karma.Server(Object.assign({}, {
    configFile: path.resolve(__dirname, baseConfig),
  }, cliOpts, opts), done).start();
}

gulp.task('test', function (callback) {
  runKarma('./h/static/scripts/karma.config.js', {singleRun:true}, callback);
});

gulp.task('test-watch', function (callback) {
  runKarma('./h/static/scripts/karma.config.js', {}, callback);
});

gulp.task('lint', function () {
  // Adapted from usage example at https://www.npmjs.com/package/gulp-eslint
  // `gulp-eslint` is loaded lazily so that it is not required during Docker image builds
  var eslint = require('gulp-eslint');
  return gulp.src(['h/static/scripts/**/*.js'])
    .pipe(eslint())
    .pipe(eslint.format())
    .pipe(eslint.failAfterError());
});
