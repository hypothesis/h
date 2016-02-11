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

/**
 * Returns true if @p err is a recognized 'expected' error.
 */
function isKnownError(err) {
  return err instanceof ExtensionError;
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
  LocalFileError: LocalFileError,
  NoFileAccessError: NoFileAccessError,
  RestrictedProtocolError: RestrictedProtocolError,
  BlockedSiteError: BlockedSiteError,
  report: report,
};
