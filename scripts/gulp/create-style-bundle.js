'use strict';

/* eslint-disable no-console */

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
  }).catch(srcErr => {
    // Rewrite error so that the message property contains the file path
    throw new Error(`SASS build error in ${srcErr.file}: ${srcErr.message}`);
  });
}

module.exports = compileSass;
