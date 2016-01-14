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
 */
function report(context, error) {
  Raven.captureException(error, {
    extra: {
      context: context,
    },
  });
}

module.exports = {
  init: init,
  angularModule: angularModule,
  setUserInfo: setUserInfo,
  report: report,
};
