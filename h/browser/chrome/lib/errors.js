'use strict';

var raven = require('../../../static/scripts/raven');

function ExtensionError(message) {
  Error.apply(this, arguments);
  this.message = message;
}
ExtensionError.prototype = Object.create(Error.prototype);

function LocalFileError(message) {
  Error.apply(this, arguments);
  this.message = message;
}
LocalFileError.prototype = Object.create(ExtensionError.prototype);

function NoFileAccessError(message) {
  Error.apply(this, arguments);
  this.message = message;
}
NoFileAccessError.prototype = Object.create(ExtensionError.prototype);

function RestrictedProtocolError(message) {
  Error.apply(this, arguments);
  this.message = message;
}
RestrictedProtocolError.prototype = Object.create(ExtensionError.prototype);

function BlockedSiteError(message) {
  Error.apply(this, arguments);
  this.message = message;
}
BlockedSiteError.prototype = Object.create(ExtensionError.prototype);

function AlreadyInjectedError(message) {
  Error.apply(this, arguments);
  this.message = message;
}
AlreadyInjectedError.prototype = Object.create(ExtensionError.prototype);

/**
 * Returns true if `err` is a recognized 'expected' error.
 */
function isKnownError(err) {
  return err instanceof ExtensionError;
}

var IGNORED_ERRORS = [
  // Errors that can happen when the tab is closed during injection
  /The tab was closed/,
  /No tab with id.*/,
  // Attempts to access pages for which Chrome does not allow scripting
  /Cannot access contents of.*/,
  /The extensions gallery cannot be scripted/,
];

/**
 * Returns true if a given `err` is anticipated during sidebar injection, such
 * as the tab being closed by the user, and should not be reported to Sentry.
 *
 * @param {{message: string}} err - The Error-like object
 */
function shouldIgnoreInjectionError(err) {
  if (IGNORED_ERRORS.some(function (pattern) {
    return err.message.match(pattern);
  })) {
    return true;
  }
  if (isKnownError(err)) {
    return true;
  }
  return false;
}

/**
 * Report an error.
 *
 * All errors are logged to the console. Additionally unexpected errors,
 * ie. those which are not instances of ExtensionError, are reported to
 * Sentry.
 *
 * @param {Error} error - The error which happened.
 * @param {string} when - Describes the context in which the error occurred.
 * @param {Object} context - Additional context for the error.
 */
function report(error, when, context) {
  console.error(when, error);
  if (!isKnownError(error)) {
    raven.report(error, when, context);
  }
}

module.exports = {
  ExtensionError: ExtensionError,
  AlreadyInjectedError: AlreadyInjectedError,
  LocalFileError: LocalFileError,
  NoFileAccessError: NoFileAccessError,
  RestrictedProtocolError: RestrictedProtocolError,
  BlockedSiteError: BlockedSiteError,
  report: report,
  shouldIgnoreInjectionError: shouldIgnoreInjectionError,
};
