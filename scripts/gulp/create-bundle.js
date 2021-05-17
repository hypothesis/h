/**
 * Shared functions for creating JS code bundles using Browserify.
 */
'use strict';

/* eslint-env node */

const fs = require('fs');
const path = require('path');

const browserify = require('browserify');
const exorcist = require('exorcist');
const log = require('fancy-log');
const mkdirp = require('mkdirp');
const uglifyify = require('uglifyify');
const watchify = require('watchify');

function streamFinished(stream) {
  return new Promise((resolve, reject) => {
    stream.on('finish', resolve);
    stream.on('error', reject);
  });
}

function waitForever() {
  return new Promise(() => {});
}

/**
 * interface BundleOptions {
 *   name: string;
 *   path: string;
 *
 *   entry?: string[];
 *   require?: string[];
 *
 *   minify?: boolean;
 * }
 *
 * interface BuildOptions {
 *   watch?: boolean;
 * }
 */

/**
 * Generates a JavaScript application or library bundle and source maps
 * for debugging.
 *
 * @param {BundleOptions} config - Configuration information for this bundle,
 *                                 specifying the name of the bundle, what
 *                                 modules to include and which code
 *                                 transformations to apply.
 * @param {BuildOptions} buildOpts
 * @return {Promise} Promise for when the bundle is fully written
 *                   if opts.watch is false or a promise that
 *                   waits forever otherwise.
 */
module.exports = function createBundle(config, buildOpts) {
  mkdirp.sync(config.path);

  buildOpts = buildOpts || { watch: false };

  const bundleOpts = {
    debug: true,

    // Browserify will try to detect and automatically provide
    // browser implementations of Node modules.
    //
    // This can bloat the bundle hugely if implementations for large
    // modules like 'Buffer' or 'crypto' are inadvertently pulled in.
    // Here we explicitly whitelist the builtins that can be used.
    //
    // In particular 'Buffer' is excluded from the list of automatically
    // detected variables.
    //
    // See node_modules/browserify/lib/builtins.js to find out which
    // modules provide the implementations of these.
    builtins: ['console', '_process', 'querystring'],
    insertGlobalVars: {
      // The Browserify polyfill for the `Buffer` global is large and
      // unnecessary, but can get pulled into the bundle by modules that can
      // optionally use it if present.
      Buffer: undefined,
      // Override the default stub for the `global` var which defaults to
      // the `global`, `self` and `window` globals in that order.
      //
      // This can break on web pages which provide their own definition of
      // `global`. See https://github.com/hypothesis/h/issues/2723
      global: function () {
        return 'typeof self !== "undefined" ? self : window';
      },
    },
  };

  if (buildOpts.watch) {
    bundleOpts.cache = {};
    bundleOpts.packageCache = {};
  }

  // Specify modules that Browserify should not parse.
  // The 'noParse' array must contain full file paths,
  // not module names.
  bundleOpts.noParse = (config.noParse || []).map(id => {
    // If package.json specifies a custom entry point for the module for
    // use in the browser, resolve that.
    const packageConfig = require('../../package.json');
    if (packageConfig.browser && packageConfig.browser[id]) {
      return require.resolve('../../' + packageConfig.browser[id]);
    } else {
      return require.resolve(id);
    }
  });

  const name = config.name;

  const bundleFileName = name + '.bundle.js';
  const bundlePath = config.path + '/' + bundleFileName;
  const sourcemapPath = bundlePath + '.map';

  const bundle = browserify([], bundleOpts);

  (config.require || []).forEach(req => {
    // When another bundle uses 'bundle.external(<module path>)',
    // the module path is rewritten relative to the
    // base directory and a '/' prefix is added, so
    // if the other bundle contains "require('./dir/module')",
    // then Browserify will generate "require('/dir/module')".
    //
    // In the bundle which provides './dir/module', we
    // therefore need to expose the module as '/dir/module'.
    if (req[0] === '.') {
      bundle.require(req, { expose: req.slice(1) });
    } else if (req[0] === '/') {
      // If the require path is absolute, the same rules as
      // above apply but the path needs to be relative to
      // the root of the repository
      const repoRootPath = path.join(__dirname, '../../');
      const relativePath = path.relative(
        path.resolve(repoRootPath),
        path.resolve(req)
      );
      bundle.require(req, { expose: '/' + relativePath });
    } else {
      // this is a package under node_modules/, no
      // rewriting required.
      bundle.require(req);
    }
  });

  bundle.add(config.entry || []);
  bundle.external(config.external || []);

  if (config.minify) {
    bundle.transform({ global: true }, uglifyify);
  }

  function build() {
    const output = fs.createWriteStream(bundlePath);
    const b = bundle.bundle();
    b.on('error', err => {
      log('Build error', err.toString());
    });
    const stream = b.pipe(exorcist(sourcemapPath)).pipe(output);
    return streamFinished(stream);
  }

  if (buildOpts.watch) {
    bundle.plugin(watchify);
    bundle.on('update', ids => {
      const start = Date.now();

      log('Source files changed', ids);
      build()
        .then(() => {
          log('Updated %s (%d ms)', bundleFileName, Date.now() - start);
        })
        .catch(err => {
          console.error('Building updated bundle failed:', err);
        });
    });
    build()
      .then(() => {
        log('Built ' + bundleFileName);
      })
      .catch(err => {
        console.error('Error building bundle:', err);
      });

    return waitForever();
  } else {
    return build();
  }
};
