'use strict';

require('core-js/es6/promise');
require('core-js/fn/object/assign');
require('core-js/fn/string');

var path = require('path');

var batch = require('gulp-batch');
var changed = require('gulp-changed');
var commander = require('commander');
var debounce = require('lodash.debounce');
var endOfStream = require('end-of-stream');
var gulp = require('gulp');
var gulpIf = require('gulp-if');
var gulpUtil = require('gulp-util');
var postcss = require('gulp-postcss');
var postcssURL = require('postcss-url');
var sass = require('gulp-sass');
var sourcemaps = require('gulp-sourcemaps');
var through = require('through2');

var createBundle = require('./scripts/gulp/create-bundle');
var manifest = require('./scripts/gulp/manifest');

var IS_PRODUCTION_BUILD = process.env.NODE_ENV === 'production';
var SCRIPT_DIR = 'build/scripts';
var STYLE_DIR = 'build/styles';
var FONTS_DIR = 'build/fonts';
var IMAGES_DIR = 'build/images';

// LiveReloadServer instance for sending messages to connected
// development clients
var liveReloadServer;
// List of file paths that changed since the last live-reload
// notification was dispatched
var liveReloadChangedFiles = [];

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

function isSASSFile(file) {
  return file.path.match(/\.scss$/);
}

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
};
var vendorModules = ['jquery', 'bootstrap', 'raven-js'];
var vendorNoParseModules = ['jquery'];

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

var appBundleBaseConfig = {
  path: SCRIPT_DIR,
  external: vendorModules,
  minify: IS_PRODUCTION_BUILD,
  noParse: vendorNoParseModules,
};

var appBundles = [{
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
}];

var appBundleConfigs = appBundles.map(function (config) {
  return Object.assign({}, appBundleBaseConfig, config);
});

gulp.task('build-app-js', ['build-vendor-js'], function () {
  return Promise.all(appBundleConfigs.map(function (config) {
    return createBundle(config);
  }));
});

gulp.task('watch-app-js', ['build-vendor-js'], function () {
  appBundleConfigs.map(function (config) {
    createBundle(config, {watch: true});
  });
});

var extensionBundleConfig = {
  name: 'extension',
  entry: './h/browser/chrome/lib/extension',
  path: SCRIPT_DIR,
  external: vendorModules,
  minify: IS_PRODUCTION_BUILD,
  noParse: vendorNoParseModules,
};

gulp.task('build-extension-js', ['build-vendor-js'], function () {
  return createBundle(extensionBundleConfig);
});

gulp.task('watch-extension-js', ['build-vendor-js'], function () {
  return createBundle(extensionBundleConfig, {watch: true});
});

var styleFiles = [
  // H
  './h/static/styles/admin.scss',
  './h/static/styles/front-page/main.css',
  './h/static/styles/help-page.scss',
  './h/static/styles/site.scss',
  './h/static/styles/old-home.scss',

  // Vendor
  './h/static/styles/vendor/icomoon.css',
  './node_modules/bootstrap/dist/css/bootstrap.css',
];

gulp.task('build-css', function () {
  // Rewrite font URLs to look for fonts in 'build/fonts' instead of
  // 'build/styles/fonts'
  function rewriteCSSURL(url) {
    return url.replace(/^fonts\//, '../fonts/');
  }

  var sassOpts = {
    outputStyle: IS_PRODUCTION_BUILD ? 'compressed' : 'nested',
  };

  var cssURLRewriter = postcssURL({
    url: rewriteCSSURL,
  });

  return gulp.src(styleFiles)
    .pipe(sourcemaps.init())
    .pipe(gulpIf(isSASSFile, sass(sassOpts).on('error', sass.logError)))
    .pipe(postcss([require('autoprefixer'), cssURLRewriter]))
    .pipe(sourcemaps.write('.'))
    .pipe(gulp.dest(STYLE_DIR));
});

gulp.task('watch-css', function () {
  var vendorCSS = styleFiles.filter(function (path) {
    return path.endsWith('.css');
  });
  var styleFileGlobs = vendorCSS.concat('./h/static/styles/**/*.scss');

  gulp.watch(styleFileGlobs, ['build-css']);
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
  gulp.src(imageFiles)
    .pipe(changed(IMAGES_DIR))
    .pipe(gulp.dest(IMAGES_DIR));
});

gulp.task('watch-images', function () {
  gulp.watch(imageFiles, ['build-images']);
});

var MANIFEST_SOURCE_FILES = 'build/@(fonts|images|scripts|styles)/*.@(js|css|woff|jpg|png|svg)';

var prevManifest = {};

/**
 * Return an array of asset paths that changed between
 * two versions of a manifest.
 */
function changedAssets(prevManifest, newManifest) {
  return Object.keys(newManifest).filter(function (asset) {
    return newManifest[asset] !== prevManifest[asset];
  });
}

var debouncedLiveReload = debounce(function () {
  // Notify dev clients about the changed assets. Note: This currently has an
  // issue that if CSS and JS are all changed in quick succession, some of the
  // assets might be empty/incomplete files that are still being generated when
  // this is invoked, causing the reload to fail.
  //
  // Live reload notifications are debounced to reduce the likelihood of this
  // happening.
  liveReloadServer.notifyChanged(liveReloadChangedFiles);
  liveReloadChangedFiles = [];
}, 250);

function triggerLiveReload(changedFiles) {
  if (!liveReloadServer) {
    return;
  }
  liveReloadChangedFiles = liveReloadChangedFiles.concat(changedFiles);
  debouncedLiveReload();
}

/**
 * Generate a JSON manifest mapping file paths to
 * URLs containing cache-busting query string parameters.
 */
function generateManifest() {
  gulp.src(MANIFEST_SOURCE_FILES)
    .pipe(manifest({name: 'manifest.json'}))
    .pipe(through.obj(function (file, enc, callback) {
      gulpUtil.log('Updated asset manifest');

      var newManifest = JSON.parse(file.contents.toString());
      var changed = changedAssets(prevManifest, newManifest);
      prevManifest = newManifest;
      triggerLiveReload(changed);

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

gulp.task('start-live-reload-server', function () {
  var LiveReloadServer = require('./scripts/gulp/live-reload-server');
  liveReloadServer = new LiveReloadServer(3000, 'http://localhost:5000');
});

gulp.task('build-app',
          ['build-app-js',
           'build-css',
           'build-fonts',
           'build-images'],
          generateManifest);

gulp.task('build',
          ['build-app-js',
           'build-extension-js',
           'build-css',
           'build-fonts',
           'build-images'],
          generateManifest);

gulp.task('watch',
          ['start-live-reload-server',
           'watch-app-js',
           'watch-extension-js',
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
      }
    },
  };

  var karma = require('karma');
  new karma.Server(Object.assign({}, {
    configFile: path.resolve(__dirname, baseConfig),
  }, cliOpts, opts), done).start();
}

gulp.task('test-app', function (callback) {
  runKarma('./h/static/scripts/karma.config.js', {singleRun:true}, callback);
});

gulp.task('test-extension', function (callback) {
  runKarma('./h/browser/chrome/karma.config.js', {singleRun:true}, callback);
});

gulp.task('test-watch-app', function (callback) {
  runKarma('./h/static/scripts/karma.config.js', {}, callback);
});

gulp.task('test-watch-extension', function (callback) {
  runKarma('./h/browser/chrome/karma.config.js', {}, callback);
});

gulp.task('upload-sourcemaps',
          ['build-app-js',
           'build-extension-js'], function () {
  var uploadToSentry = require('./scripts/gulp/upload-to-sentry');

  var opts = {
    key: getEnv('SENTRY_API_KEY'),
    organization: getEnv('SENTRY_ORGANIZATION'),
  };
  var projects = getEnv('SENTRY_PROJECTS').split(',');
  var release = getEnv('SENTRY_RELEASE_VERSION');

  return gulp.src(['build/scripts/*.js', 'build/scripts/*.map'])
    .pipe(uploadToSentry(opts, projects, release));
});
