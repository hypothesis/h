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

var createBundle = require('./scripts/gulp/createBundle');

var PRODUCTION_BUILD = process.env.NODE_ENV === 'production';
var SCRIPT_DIR = 'build/scripts';
var STYLE_DIR = 'build/styles';
var FONTS_DIR = 'build/fonts';
var IMAGES_DIR = 'build/images';

var vendorBundles = require('./vendor-bundles');

function bundleNames(bundles) {
  return bundles.map(function (bundle) {
    if (typeof bundle === 'string') {
      return bundle;
    } else {
      return bundle.name;
    }
  });
}

function isSASS(file) {
  return file.path.match(/\.scss$/);
}

var noParseModules = Object.keys(vendorBundles).reduce(function (modules, name) {
  return modules.concat(vendorBundles[name].filter(function (bundle) {
    return bundle.noParse;
  }).map(function (bundle) {
    if (bundle.name[0] === '.') {
      return require.resolve(bundle.name);
    } else {
      return bundle.name;
    }
  }));
}, []);

var vendorModules = Object.keys(vendorBundles).reduce(function (deps, key) {
  return deps.concat(bundleNames(vendorBundles[key]));
}, []);

gulp.task('build-vendor-js', function (done) {
  var finished = [];
  Object.keys(vendorBundles).forEach(function (name) {
    finished.push(createBundle({
      name: name,
      require: bundleNames(vendorBundles[name]),
      minify: PRODUCTION_BUILD,
      path: SCRIPT_DIR,
      noParse: noParseModules,
    }));
  });
  return Promise.all(finished);
});

var baseOpts = {
  path: SCRIPT_DIR,
  external: vendorModules,
  minify: PRODUCTION_BUILD,
  noParse: noParseModules,
};

var appBundleOpts = Object.assign({}, baseOpts, {
  name: 'app',
  transforms: ['coffee'],
  entry: './h/static/scripts/app.coffee',
});

var extensionBundleOpts = Object.assign({}, baseOpts, {
  name: 'extension',
  entry: './h/browser/chrome/lib/extension',
});

var injectorBundleOpts = Object.assign({}, baseOpts, {
  name: 'injector',
  entry: './h/static/scripts/annotator/main',
  transforms: ['coffee'],
});

var siteBundleOpts = Object.assign({}, baseOpts, {
  name: 'site',
  entry: './h/static/scripts/site',
});

var bundles = [
  appBundleOpts,
  extensionBundleOpts,
  siteBundleOpts,
  injectorBundleOpts
];

gulp.task('build-app', ['build-vendor-js'], function () {
  return Promise.all(bundles.map(function (bundle) {
    return createBundle(bundle);
  }));
});

gulp.task('watch-app', ['build-vendor-js'], function (done) {
  bundles.map(function (bundle) {
    createBundle(Object.assign({}, bundle, {watch: true}));
  });
});

var styleFiles = [
  // H
  './h/static/styles/app.scss',
  './h/static/styles/annotator/inject.scss',
  './h/static/styles/annotator/pdfjs-overrides.scss',
  './h/static/styles/site.scss',
  './h/static/styles/help-page.scss',
  './h/static/styles/admin.scss',
  './h/static/styles/front-page/main.css',

  // Vendor
  './h/static/styles/vendor/angular-csp.css',
  './node_modules/angular-toastr/dist/angular-toastr.css',
  './h/static/styles/vendor/icomoon.css',
  './h/static/styles/vendor/katex.min.css',

  // Admin
  './node_modules/bootstrap/dist/css/bootstrap.css',
];

gulp.task('build-css', function () {
  var sassOpts = {
    outputStyle: PRODUCTION_BUILD ? 'compressed' : 'nested',
    includePaths: ['node_modules/compass-mixins/lib/'],
  };

  return gulp.src(styleFiles)
    .pipe(changed(STYLE_DIR, {extension: '.css'}))
    .pipe(sourcemaps.init())
    .pipe(gulpIf(isSASS, sass(sassOpts).on('error', sass.logError)))
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

gulp.task('build', ['build-app', 'build-css', 'build-fonts', 'build-images']);
gulp.task('watch', ['watch-app', 'watch-css', 'watch-fonts', 'watch-images']);
