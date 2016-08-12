'use strict';

/* eslint-disable no-console */

/* global Set */

var fs = require('fs');
var path = require('path');

var autoprefixer = require('autoprefixer');
var gulpUtil = require('gulp-util');
var postcss = require('postcss');
var postcssURL = require('postcss-url');
var sass = require('node-sass');

var log = gulpUtil.log;

/**
 * Compile a SASS file and postprocess the result.
 *
 * @param {options} options - Object specifying the input and output paths and
 *                  whether to minify the result.
 * @return {Promise} Promise for completion of the build.
 */
function compileSass(options) {
  var sourcemapPath = options.output + '.map';

  var postcssPlugins = [autoprefixer];

  if (options.urlRewriter) {
    postcssPlugins.push(postcssURL({
      url: options.urlRewriter,
    }));
  }

  var start = Date.now();
  var sassBuild = new Promise((resolve, reject) => {
    sass.render({
      file: options.input,
      importer: options.onImport,
      includePaths: [path.dirname(options.input)],
      outputStyle: options.minify ? 'compressed' : 'nested',
      sourceMap: sourcemapPath,
    }, (err, result) => {
      if (err) {
        reject(err);
      } else {
        resolve(result);
      }
    });
  });

  return sassBuild.then(result => {
    return postcss(postcssPlugins)
      .process(result.css, {
        from: options.output,
        to: options.output,
        map: {
          inline: false,
          prev: result.map.toString(),
        },
      });
  }).then(result => {
    fs.writeFileSync(options.output, result.css);
    fs.writeFileSync(sourcemapPath, result.map.toString());

    return {
      stats: {
        duration: Date.now() - start,
      },
    };
  });
}

function logError(err) {
  log(`SASS build error: ${err.message}`);
}

/**
 * Update the set of files watched by a chokidar file watcher.
 *
 * @param {FSWatcher} watcher - chokidar file watcher
 * @param {Set.<string>} currentPaths - Current set of watched files
 * @param {Set.<string>} newPaths - New set of files to watch
 */
function updateWatchedFiles(watcher, currentPaths, newPaths) {
  newPaths.forEach(path => {
    if (!currentPaths.has(path)) {
      watcher.add(path);
    }
  });
  currentPaths.forEach(path => {
    if (!newPaths.has(path)) {
      watcher.unwatch(path);
    }
  });
}

/**
 * Compile a SASS file and rebuild when any of the included files changes.
 *
 * This is similar to `watchify` for Browserify JS bundles, in that it makes
 * use of the dependency information (in the form of `@import` statements) in
 * the root SCSS file to know which files to watch. As a result, it will
 * automatically start watching newly added imports.
 *
 * See `compileSass()` for a description of the `options` parameter.
 */
function compileSassAndWatchForChanges(options) {
  // chokidar dependency is loaded lazily so that it is not required in Docker
  // image builds
  var chokidar = require('chokidar');

  var watcher = chokidar.watch(options.input);
  var watchedFiles = new Set();

  var isBuilding = false;
  var pendingBuild = false;

  function rebuild() {
    pendingBuild = false;
    isBuilding = true;

    compileSass(options)
      .then(result => {
        log(`Built ${options.output} (${result.stats.duration}ms)`);
        var includedFiles = new Set(result.stats.includedFiles);
        updateWatchedFiles(watcher, watchedFiles, includedFiles);
        watchedFiles = includedFiles;
      })
      .catch(logError)
      .then(() => {
        isBuilding = false;
        if (pendingBuild) {
          rebuild();
        }
      });
  }

  watcher.on('change', path => {
    log(`${path} changed. Rebuilding ${options.output}`);

    if (!isBuilding) {
      rebuild();
    } else {
      pendingBuild = true;
    }
  });

  rebuild();
}

/**
 * Create a CSS bundle from a SASS input file.
 */
function createStyleBundle(options) {
  if (options.watch) {
    compileSassAndWatchForChanges(options);

    // A `watch` build never terminates
    return new Promise(() => {});
  } else {
    return compileSass(options);
  }
}

module.exports = createStyleBundle;
