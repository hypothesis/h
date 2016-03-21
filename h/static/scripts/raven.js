'use strict';

/**
 * This module configures Raven for reporting crashes
 * to Sentry.
 *
 * Logging requires the Sentry DSN and Hypothesis
 * version to be provided via the app's settings object.
 *
 * It also exports an Angular module via angularModule() which integrates
 * error logging into any Angular application that it is added to
 * as a dependency.
 */

require('core-js/fn/object/assign');

var Raven = require('raven-js');

// This is only used in apps where Angular is used,
// but is required globally due to
// https://github.com/thlorenz/proxyquireify/issues/40
//
// Fortunately it does not pull in Angular as a dependency but returns
// a function that takes it as an input argument.
var angularPlugin = require('raven-js/plugins/angular');

/**
 * Returns the input URL if it is an HTTP URL or the filename part of the URL
 * otherwise.
 *
 * @param {string} url - The script URL associated with an exception stack
 *                       frame.
 */
function convertLocalURLsToFilenames(url) {
  if (!url) {
    return url;
  }

  if (url.match(/https?:/)) {
    return url;
  }

  // Strip the query string (which is used as a cache buster)
  // and extract the filename from the URL
  return url.replace(/\?.*/,'').split('/').slice(-1)[0];
}

/**
 * Return a transformed version of `data` with local URLs replaced
 * with filenames.
 *
 * In environments where the client is served from a local URL,
 * eg. chrome-extension://<ID>/scripts/bundle.js, the script URL
 * and the sourcemap it references will not be accessible to Sentry.
 *
 * Therefore on the client we replace references to such URLs with just
 * the filename part and then as part of the release process, upload both
 * the source file and the source map to Sentry.
 *
 * Using just the filename allows us to upload a single set of source files
 * and sourcemaps for a release though a given release of H might be served
 * from multiple actual URLs (eg. different browser extensions).
 */
function translateSourceURLs(data) {
  try {
    var frames = data.exception.values[0].stacktrace.frames;
    frames.forEach(function (frame) {
      frame.filename = convertLocalURLsToFilenames(frame.filename);
    });
    data.culprit = frames[0].filename;
  } catch (err) {
    console.warn('Failed to normalize error stack trace', err, data);
  }
  return data;
}

function init(config) {
  Raven.config(config.dsn, {
    release: config.release,
    dataCallback: translateSourceURLs,
  }).install();
  installUnhandledPromiseErrorHandler();
}

function setUserInfo(info) {
  if (info) {
    Raven.setUserContext(info);
  } else {
    Raven.setUserContext();
  }
}

/**
 * Initializes and returns the Angular module which provides
 * a custom wrapper around Angular's $exceptionHandler service,
 * logging any exceptions passed to it using Sentry.
 *
 * This must be invoked _after_ Raven is configured using init().
 */
function angularModule(angular) {
  var prevCallback = Raven._globalOptions.dataCallback;
  angularPlugin(Raven, angular);

  // Hack: Ensure that both our data callback and the one provided by
  // the Angular plugin are run when submitting errors.
  //
  // The Angular plugin replaces any previously installed
  // data callback with its own which does not in turn call the
  // previously registered callback that we registered when calling
  // Raven.config().
  //
  // See https://github.com/getsentry/raven-js/issues/522
  var angularCallback = Raven._globalOptions.dataCallback;
  Raven.setDataCallback(function (data) {
    return angularCallback(prevCallback(data));
  });
  return angular.module('ngRaven');
}

/**
 * Report an error to Sentry.
 *
 * @param {Error} error - An error object describing what went wrong
 * @param {string} when - A string describing the context in which
 *                        the error occurred.
 * @param {Object} [context] - A JSON-serializable object containing additional
 *                             information which may be useful when
 *                             investigating the error.
 */
function report(error, when, context) {
  if (!(error instanceof Error)) {
    // If the passed object is not an Error, raven-js
    // will serialize it using toString() which produces unhelpful results
    // for objects that do not provide their own toString() implementations.
    //
    // If the error is a plain object or non-Error subclass with a message
    // property, such as errors returned by chrome.extension.lastError,
    // use that instead.
    if (typeof error === 'object' && error.message) {
      error = error.message;
    }
  }

  var extra = Object.assign({ when: when }, context);
  Raven.captureException(error, { extra: extra });
}

/**
 * Installs a handler to catch unhandled rejected promises.
 *
 * For this to work, the browser or the Promise polyfill must support
 * the unhandled promise rejection event (Chrome >= 49). On other browsers,
 * the rejections will simply go unnoticed. Therefore, app code _should_
 * always provide a .catch() handler on the top-most promise chain.
 *
 * See https://github.com/getsentry/raven-js/issues/424
 * and https://www.chromestatus.com/feature/4805872211460096
 *
 * It is possible that future versions of Raven JS may handle these events
 * automatically, in which case this code can simply be removed.
 */
function installUnhandledPromiseErrorHandler() {
  window.addEventListener('unhandledrejection', function (event) {
    if (event.reason) {
      report(event.reason, 'Unhandled Promise rejection');
    }
  });
}

module.exports = {
  init: init,
  angularModule: angularModule,
  setUserInfo: setUserInfo,
  report: report,
};
