'use strict';

/* eslint-env node */
/* eslint-disable no-var, prefer-arrow-callback */

var path = require('path');

var changed = require('gulp-changed');
var commander = require('commander');
var gulp = require('gulp');
var gulpIf = require('gulp-if');
var log = require('gulplog');
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
    log.info(`Running tests matching pattern /${commander.grep}/`);
  }

  return {
    grep: commander.grep,
  };
}

var taskArgs = parseCommandLine();

var vendorBundles = {
  jquery: ['jquery'],
  bootstrap: ['bootstrap'],
  raven: ['raven-js'],
  unorm: ['unorm'],
};
var vendorModules = ['jquery', 'bootstrap', 'raven-js', 'unorm'];
var vendorNoParseModules = ['jquery', 'unorm'];

// Builds the bundles containing vendor JS code
gulp.task('build-vendor-js', function() {
  var finished = [];
  Object.keys(vendorBundles).forEach(function(name) {
    finished.push(
      createBundle({
        name: name,
        require: vendorBundles[name],
        minify: IS_PRODUCTION_BUILD,
        path: SCRIPT_DIR,
        noParse: vendorNoParseModules,
      })
    );
  });
  return Promise.all(finished);
});

var bundleBaseConfig = {
  path: SCRIPT_DIR,
  external: vendorModules,
  minify: IS_PRODUCTION_BUILD,
  noParse: vendorNoParseModules,
};

var bundles = [
  {
    // Public-facing website
    name: 'site',
    entry: './h/static/scripts/site',
  },
  {
    // Admin areas of the site
    name: 'admin-site',
    entry: './h/static/scripts/admin-site',
  },
  {
    // Header script inserted inline at the top of the page
    name: 'header',
    entry: './h/static/scripts/header',
  },
  {
    // Helper script for the OAuth post-authorization page.
    name: 'post-auth',
    entry: './h/static/scripts/post-auth',
  },
];

var bundleConfigs = bundles.map(function(config) {
  return Object.assign({}, bundleBaseConfig, config);
});

gulp.task(
  'build-js',
  gulp.series(['build-vendor-js'], function() {
    return Promise.all(
      bundleConfigs.map(function(config) {
        return createBundle(config);
      })
    );
  })
);

gulp.task(
  'watch-js',
  gulp.series(['build-vendor-js'], function() {
    return bundleConfigs.map(config => createBundle(config, { watch: true }));
  })
);

// Rewrite font URLs to look for fonts in 'build/fonts' instead of
// 'build/styles/fonts'
function rewriteCSSURL(asset) {
  return asset.url.replace(/^fonts\//, '../fonts/');
}

gulp.task('build-vendor-css', function() {
  var vendorCSSFiles = [
    // Icon font
    './h/static/styles/vendor/icomoon.css',
    './node_modules/bootstrap/dist/css/bootstrap.css',
  ];

  var cssURLRewriter = postcssURL({
    url: rewriteCSSURL,
  });

  return gulp
    .src(vendorCSSFiles)
    .pipe(newer(STYLE_DIR))
    .pipe(postcss([cssURLRewriter]))
    .pipe(gulp.dest(STYLE_DIR));
});

var styleBundleEntryFiles = [
  './h/static/styles/admin.scss',
  './h/static/styles/help-page.scss',
  './h/static/styles/site.scss',
];

function buildStyleBundle(entryFile) {
  return createStyleBundle({
    input: entryFile,
    output: './build/styles/' + path.basename(entryFile, '.scss') + '.css',
    minify: IS_PRODUCTION_BUILD,
    urlRewriter: rewriteCSSURL,
  });
}

gulp.task(
  'build-css',
  gulp.series(['build-vendor-css'], function() {
    return Promise.all(styleBundleEntryFiles.map(buildStyleBundle));
  })
);

gulp.task('watch-css', function() {
  gulp.watch(
    'h/static/styles/**/*.scss',
    { ignoreInitial: false },
    gulp.series('build-css')
  );
});

var fontFiles = 'h/static/styles/vendor/fonts/*.woff';

gulp.task('build-fonts', function() {
  return gulp
    .src(fontFiles)
    .pipe(changed(FONTS_DIR))
    .pipe(gulp.dest(FONTS_DIR));
});

gulp.task('watch-fonts', function() {
  gulp.watch(fontFiles, gulp.series('build-fonts'));
});

var imageFiles = 'h/static/images/**/*';
gulp.task('build-images', function() {
  var shouldMinifySVG = function(file) {
    return IS_PRODUCTION_BUILD && file.path.match(/\.svg$/);
  };

  // See https://github.com/ben-eb/gulp-svgmin#plugins
  var svgminConfig = {
    plugins: [
      {
        // svgo removes `viewBox` by default, which breaks scaled rendering of
        // the SVG.
        //
        // See https://github.com/svg/svgo/issues/1128
        removeViewBox: false,
      },
    ],
  };

  return gulp
    .src(imageFiles)
    .pipe(changed(IMAGES_DIR))
    .pipe(gulpIf(shouldMinifySVG, svgmin(svgminConfig)))
    .pipe(gulp.dest(IMAGES_DIR));
});

gulp.task('watch-images', function() {
  gulp.watch(imageFiles, gulp.series('build-images'));
});

var MANIFEST_SOURCE_FILES = 'build/@(fonts|images|scripts|styles)/**/*.*';

/**
 * Generate a JSON manifest mapping file paths to
 * URLs containing cache-busting query string parameters.
 */
function generateManifest() {
  return gulp
    .src(MANIFEST_SOURCE_FILES)
    .pipe(manifest({ name: 'manifest.json' }))
    .pipe(
      through.obj(function(file, enc, callback) {
        log.info('Updated asset manifest');
        this.push(file);
        callback();
      })
    )
    .pipe(gulp.dest('build/'));
}

gulp.task('watch-manifest', function() {
  gulp.watch(MANIFEST_SOURCE_FILES, generateManifest);
});

gulp.task(
  'build',
  gulp.series(
    ['build-js', 'build-css', 'build-fonts', 'build-images'],
    generateManifest
  )
);
gulp.task(
  'watch',
  gulp.parallel([
    'watch-js',
    'watch-css',
    'watch-fonts',
    'watch-images',
    'watch-manifest',
  ])
);

function runKarma(baseConfig, opts, done) {
  // See https://github.com/karma-runner/karma-mocha#configuration
  var cliOpts = {
    client: {
      mocha: {
        grep: taskArgs.grep,
      },
    },
  };

  var karma = require('karma');
  new karma.Server(
    Object.assign(
      {},
      {
        configFile: path.resolve(__dirname, baseConfig),
      },
      cliOpts,
      opts
    ),
    done
  ).start();
}

gulp.task('test', function(callback) {
  runKarma('./h/static/scripts/karma.config.js', { singleRun: true }, callback);
});

gulp.task('test-watch', function(callback) {
  runKarma('./h/static/scripts/karma.config.js', {}, callback);
});
