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

var Raven = require('raven-js')

var enabled = false;

function init(config) {
  Raven.config(config.dsn, {
    release: config.release,
  }).install();
  enabled = true;
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
 * logging any exceptions passed to it using Sentry
 */
function angularModule() {
  if (enabled) {
    if (window.angular) {
      var angularPlugin = require('raven-js/plugins/angular');
      angularPlugin(Raven, angular);
    }
  } else {
    // define a stub module in environments where Raven is not enabled
    angular.module('ngRaven', []);
  }
  return angular.module('ngRaven');
}

/**
 * Report an error to Sentry.
 *
 * @param {string} context - A string describing the context in which
 *                           the error occurred.
 * @param {Error} error - An error object describing what went wrong
 *
 * @param {details} Object - A JSON-serializable object containing additional
 *                          information which may be useful when investigating
 *                          the error.
 */
function report(context, error, details) {
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

  Raven.captureException(error, {
    extra: {
      context: context,
      details: details,
    },
  });
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
      report('Unhandled Promise rejection', event.reason);
    }
  });
}

module.exports = {
  init: init,
  angularModule: angularModule,
  setUserInfo: setUserInfo,
  report: report,
};
