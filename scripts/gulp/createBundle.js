'use strict';

var coffeeify = require('coffeeify');
var browserify = require('browserify');
var exorcist = require('exorcist');
var fs = require('fs');
var mkdirp = require('mkdirp');
var uglifyify = require('uglifyify');
var watchify = require('watchify');
var gulpUtil = require('gulp-util');

var log = gulpUtil.log;

function streamFinished(stream) {
  return new Promise(function (resolve, reject) {
    stream.on('finish', resolve);
    stream.on('error', reject);
  });
}

function waitForever() {
  return new Promise(function (resolve, reject) {});
}

/**
 * type Transform = 'coffee';
 *
 * interface BundleOptions {
 *   name: string;
 *   path: string;
 *
 *   entry?: string[];
 *   require?: string[];
 *   transforms: Transform[];
 *
 *   watch?: boolean;
 *   minify?: boolean;
 * }
 */

/**
 * Bundles the JavaScript for an application.
 *
 * @param {BundleOptions} opts
 * @return {Promise} Promise for when the bundle is fully written
 *                   if opts.watch is false or a promise that
 *                   waits forever otherwise.
 */
module.exports = function createBundle(opts) {
  mkdirp.sync(opts.path);

  var bundleOpts = {
    debug: true,
    extensions: ['.coffee'],
  };

  if (opts.watch) {
    bundleOpts.cache = {};
    bundleOpts.packageCache = {};
  }

  // Skip parsing of large modules.
  // The 'noParse' array must contain full file paths,
  // not module names.
  bundleOpts.noParse = (opts.noParse || []).map(function (id) {
    return require.resolve(id);
  });

  var name = opts.name;
  var path = opts.path;

  var bundleFileName = name + '.bundle.js';
  var bundlePath = path + '/' + bundleFileName;
  var sourcemapPath = bundlePath + '.map';

  var bundle = browserify([], bundleOpts);

  (opts.require || []).forEach(function (req) {
    // When another bundle uses 'bundle.external(<module path>)',
    // the module path is rewritten relative to the
    // base directory and a '/' prefix is added, so
    // if the other bundle contains "require('./dir/module')",
    // then Browserify will generate "require('/dir/module')".
    //
    // In the bundle which provides './dir/module', we
    // therefore need to expose the module as '/dir/module'.
    if (req[0] == '.') {
      bundle.require(req, {expose: req.slice(1)});
    } else {
      // this is a package under node_modules/, no
      // rewriting required.
      bundle.require(req);
    }
  });

  bundle.add(opts.entry || []);
  bundle.external(opts.external || []);

  (opts.transforms || []).forEach(function (transform) {
    if (transform === 'coffee') {
      bundle.transform(coffeeify);
    }
  });

  if (opts.minify) {
    bundle.transform({global: true}, uglifyify);
  }

  function build() {
    var output = fs.createWriteStream(bundlePath);
    var b = bundle.bundle()
    b.on('error', function (err) {
      log('Build error', err.toString());
    });
    var stream = b.pipe(exorcist(sourcemapPath))
                  .pipe(output);
    return streamFinished(stream);
  }

  if (opts.watch) {
    bundle.plugin(watchify);
    bundle.on('update', function (ids) {
      var start = Date.now();

      log('Source files changed', ids);
      build().then(function () {
        log('Updated %s (%d ms)', bundleFileName, Date.now() - start);
      }).catch(function (err) {
        console.error('Building updated bundle failed:', err);
      });
    });
    build().then(function () {
      log('Built ' + bundleFileName);
    }).catch(function (err) {
      console.error('Error building bundle:', err);
    });

    return waitForever();
  } else {
    return build();
  }
}

