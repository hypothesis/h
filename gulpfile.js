'use strict';

/* eslint-env node */

const path = require('path');

const changed = require('gulp-changed');
const commander = require('commander');
const gulp = require('gulp');
const gulpIf = require('gulp-if');
const log = require('fancy-log');
const postcss = require('gulp-postcss');
const postcssURL = require('postcss-url');
const svgmin = require('gulp-svgmin');
const through = require('through2');

const createBundle = require('./scripts/gulp/create-bundle');
const createStyleBundle = require('./scripts/gulp/create-style-bundle');
const manifest = require('./scripts/gulp/manifest');

const IS_PRODUCTION_BUILD = process.env.NODE_ENV === 'production';
const SCRIPT_DIR = 'build/scripts';
const STYLE_DIR = 'build/styles';
const FONTS_DIR = 'build/fonts';
const IMAGES_DIR = 'build/images';

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

const taskArgs = parseCommandLine();

const vendorBundles = {
  jquery: ['jquery'],
  bootstrap: ['bootstrap'],
  raven: ['raven-js'],
};
const vendorModules = ['jquery', 'bootstrap', 'raven-js'];
const vendorNoParseModules = ['jquery'];

// Builds the bundles containing vendor JS code
gulp.task('build-vendor-js', () => {
  const finished = [];
  Object.keys(vendorBundles).forEach(name => {
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

const bundleBaseConfig = {
  path: SCRIPT_DIR,
  external: vendorModules,
  minify: IS_PRODUCTION_BUILD,
  noParse: vendorNoParseModules,
};

const bundles = [
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

const bundleConfigs = bundles.map(config => {
  return Object.assign({}, bundleBaseConfig, config);
});

gulp.task(
  'build-js',
  gulp.series(['build-vendor-js'], () => {
    return Promise.all(
      bundleConfigs.map(config => {
        return createBundle(config);
      })
    );
  })
);

gulp.task(
  'watch-js',
  gulp.series(['build-vendor-js'], () => {
    return bundleConfigs.map(config => createBundle(config, { watch: true }));
  })
);

// Rewrite font URLs to look for fonts in 'build/fonts' instead of
// 'build/styles/fonts'
function rewriteCSSURL(asset) {
  return asset.url.replace(/^fonts\//, '../fonts/');
}

gulp.task('build-vendor-css', () => {
  const vendorCSSFiles = [
    // Icon font
    './h/static/styles/vendor/icomoon.css',
    './node_modules/bootstrap/dist/css/bootstrap.css',
  ];

  const cssURLRewriter = postcssURL({
    url: rewriteCSSURL,
  });

  return gulp
    .src(vendorCSSFiles)
    .pipe(postcss([cssURLRewriter]))
    .pipe(gulp.dest(STYLE_DIR));
});

const styleBundleEntryFiles = [
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
  gulp.series(['build-vendor-css'], () => {
    return Promise.all(styleBundleEntryFiles.map(buildStyleBundle));
  })
);

gulp.task('watch-css', () => {
  gulp.watch(
    'h/static/styles/**/*.scss',
    { ignoreInitial: false },
    gulp.series('build-css')
  );
});

const fontFiles = 'h/static/styles/vendor/fonts/*.woff';

gulp.task('build-fonts', () => {
  return gulp
    .src(fontFiles)
    .pipe(changed(FONTS_DIR))
    .pipe(gulp.dest(FONTS_DIR));
});

gulp.task('watch-fonts', () => {
  gulp.watch(fontFiles, gulp.series('build-fonts'));
});

const imageFiles = 'h/static/images/**/*';
gulp.task('build-images', () => {
  const shouldMinifySVG = function (file) {
    return IS_PRODUCTION_BUILD && file.path.match(/\.svg$/);
  };

  // See https://github.com/ben-eb/gulp-svgmin#plugins
  const svgminConfig = {
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

gulp.task('watch-images', () => {
  gulp.watch(imageFiles, gulp.series('build-images'));
});

const MANIFEST_SOURCE_FILES = 'build/@(fonts|images|scripts|styles)/**/*.*';

/**
 * Generate a JSON manifest mapping file paths to
 * URLs containing cache-busting query string parameters.
 */
function generateManifest() {
  return gulp
    .src(MANIFEST_SOURCE_FILES)
    .pipe(manifest({ name: 'manifest.json' }))
    .pipe(
      through.obj(function (file, enc, callback) {
        log.info('Updated asset manifest');
        this.push(file);
        callback();
      })
    )
    .pipe(gulp.dest('build/'));
}

gulp.task('watch-manifest', () => {
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
  const cliOpts = {
    client: {
      mocha: {
        grep: taskArgs.grep,
      },
    },
    ...opts,
  };

  const karma = require('karma');
  new karma.Server(
    karma.config.parseConfig(path.resolve(__dirname, baseConfig), cliOpts),
    done
  ).start();
}

gulp.task('test', callback => {
  runKarma('./h/static/scripts/karma.config.js', { singleRun: true }, callback);
});

gulp.task('test-watch', callback => {
  runKarma('./h/static/scripts/karma.config.js', {}, callback);
});
