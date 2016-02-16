require('core-js/es6/promise');
require('core-js/fn/object/assign');
require('core-js/fn/string');

var path = require('path');

var changed = require('gulp-changed');
var gulp = require('gulp');
var gulpIf = require('gulp-if');
var sass = require('gulp-sass');
var postcss = require('gulp-postcss');
var sourcemaps = require('gulp-sourcemaps');

var createBundle = require('./scripts/gulp/create-bundle');
var vendorBundles = require('./scripts/gulp/vendor-bundles');

var IS_PRODUCTION_BUILD = process.env.NODE_ENV === 'production';
var SCRIPT_DIR = 'build/scripts';
var STYLE_DIR = 'build/styles';
var FONTS_DIR = 'build/fonts';
var IMAGES_DIR = 'build/images';

function isSASSFile(file) {
  return file.path.match(/\.scss$/);
}

/** A list of all modules included in vendor bundles. */
var vendorModules = Object.keys(vendorBundles.bundles)
  .reduce(function (deps, key) {
  return deps.concat(vendorBundles.bundles[key]);
}, []);

/** Builds the bundles containing vendor JS code */
gulp.task('build-vendor-js', function (done) {
  var finished = [];
  Object.keys(vendorBundles.bundles).forEach(function (name) {
    finished.push(createBundle({
      name: name,
      require: vendorBundles.bundles[name],
      minify: IS_PRODUCTION_BUILD,
      path: SCRIPT_DIR,
      noParse: vendorBundles.noParseModules,
    }));
  });
  return Promise.all(finished);
});

var appBundleBaseConfig = {
  path: SCRIPT_DIR,
  external: vendorModules,
  minify: IS_PRODUCTION_BUILD,
  noParse: vendorBundles.noParseModules,
};

var appBundles = [{
  // The sidebar application for displaying and editing annotations
  name: 'app',
  transforms: ['coffee'],
  entry: './h/static/scripts/app.coffee',
},{
  // Browser extension background script
  name: 'extension',
  entry: './h/browser/chrome/lib/extension',
},{
  // The Annotator library which provides annotation controls on
  // the page and sets up the sidebar
  name: 'injector',
  entry: './h/static/scripts/annotator/main',
  transforms: ['coffee'],
},{
  // Public-facing website
  name: 'site',
  entry: './h/static/scripts/site',
},{
  // Admin areas of the site
  name: 'admin-site',
  entry: './h/static/scripts/admin-site',
}];

var appBundleConfigs = appBundles.map(function (config) {
  return Object.assign({}, appBundleBaseConfig, config);
});

gulp.task('build-app-js', ['build-vendor-js'], function () {
  return Promise.all(appBundleConfigs.map(function (config) {
    return createBundle(config);
  }));
});

gulp.task('watch-app-js', ['build-vendor-js'], function (done) {
  appBundleConfigs.map(function (config) {
    createBundle(config, {watch: true});
  });
});

var styleFiles = [
  // H
  './h/static/styles/admin.scss',
  './h/static/styles/annotator/inject.scss',
  './h/static/styles/annotator/pdfjs-overrides.scss',
  './h/static/styles/app.scss',
  './h/static/styles/front-page/main.css',
  './h/static/styles/help-page.scss',
  './h/static/styles/site.scss',

  // Vendor
  './h/static/styles/vendor/angular-csp.css',
  './h/static/styles/vendor/icomoon.css',
  './h/static/styles/vendor/katex.min.css',
  './node_modules/angular-toastr/dist/angular-toastr.css',
  './node_modules/bootstrap/dist/css/bootstrap.css',
];

gulp.task('build-css', function () {
  var sassOpts = {
    outputStyle: IS_PRODUCTION_BUILD ? 'compressed' : 'nested',
    includePaths: ['node_modules/compass-mixins/lib/'],
  };

  return gulp.src(styleFiles)
    .pipe(changed(STYLE_DIR, {extension: '.css'}))
    .pipe(sourcemaps.init())
    .pipe(gulpIf(isSASSFile, sass(sassOpts).on('error', sass.logError)))
    .pipe(postcss([require('autoprefixer')]))
    .pipe(sourcemaps.write('.'))
    .pipe(gulp.dest(STYLE_DIR));
});

gulp.task('watch-css', function () {
  gulp.watch(styleFiles, ['build-css']);
});

var fontFiles = 'h/static/styles/vendor/fonts/*.woff';

gulp.task('build-fonts', function () {
  gulp.src(fontFiles)
    .pipe(changed(FONTS_DIR))
    .pipe(gulp.dest(FONTS_DIR))
});

gulp.task('watch-fonts', function () {
  gulp.watch(fontFiles, ['build-fonts']);
});

var imageFiles = 'h/static/images/**/*';
gulp.task('build-images', function () {
  gulp.src(imageFiles)
    .pipe(changed(IMAGES_DIR))
    .pipe(gulp.dest(IMAGES_DIR))
});

gulp.task('watch-images', function () {
  gulp.watch(imageFiles, ['build-images']);
});

gulp.task('build', ['build-app-js', 'build-css',
                    'build-fonts', 'build-images']);
gulp.task('watch', ['watch-app-js', 'watch-css',
                    'watch-fonts', 'watch-images']);
