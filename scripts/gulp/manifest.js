'use strict';

var path = require('path');
var crypto = require('crypto');

var through = require('through2');
var VinylFile = require('vinyl');

/**
 * Gulp plugin that generates a cache-busting manifest file.
 *
 * Returns a function that creates a stream which takes
 * a stream of Vinyl files as inputs and outputs a JSON
 * manifest mapping input paths (eg. "scripts/foo.js")
 * to URLs with cache-busting query parameters (eg. "scripts/foo.js?af95bd").
 */
module.exports = function (opts) {
  var manifest = {};

  return through.obj(function (file, enc, callback) {
    var hash = crypto.createHash('sha1');
    hash.update(file.contents);

    var hashSuffix = hash.digest('hex').slice(0, 6);
    var relPath = path.relative('build/', file.path);
    manifest[relPath] = relPath + '?' + hashSuffix;

    callback();
  }, function (callback) {
    var manifestFile = new VinylFile({
      path: opts.name,
      contents: Buffer.from(JSON.stringify(manifest, null, 2), 'utf-8'),
    });
    this.push(manifestFile);
    callback();
  });
};
