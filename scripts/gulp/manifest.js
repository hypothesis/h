'use strict';

/* eslint-env node */

const path = require('path');
const crypto = require('crypto');

const through = require('through2');
const VinylFile = require('vinyl');

/**
 * Gulp plugin that generates a cache-busting manifest file.
 *
 * Returns a function that creates a stream which takes
 * a stream of Vinyl files as inputs and outputs a JSON
 * manifest mapping input paths (eg. "scripts/foo.js")
 * to URLs with cache-busting query parameters (eg. "scripts/foo.js?af95bd").
 */
module.exports = function (opts) {
  const manifest = {};

  return through.obj(
    (file, enc, callback) => {
      const hash = crypto.createHash('sha1');
      hash.update(file.contents);

      const hashSuffix = hash.digest('hex').slice(0, 6);
      const relPath = path.relative('build/', file.path);
      manifest[relPath] = relPath + '?' + hashSuffix;

      callback();
    },
    function (callback) {
      const manifestFile = new VinylFile({
        path: opts.name,
        contents: Buffer.from(JSON.stringify(manifest, null, 2), 'utf-8'),
      });
      this.push(manifestFile);
      callback();
    }
  );
};
