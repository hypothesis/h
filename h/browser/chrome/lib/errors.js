function ExtensionError(message) {
  Error.apply(this, arguments);
  this.message = message;
}
ExtensionError.prototype = Object.create(Error);

function LocalFileError(message) {
  Error.apply(this, arguments);
  this.message = message;
}
LocalFileError.prototype = Object.create(ExtensionError);

function NoFileAccessError(message) {
  Error.apply(this, arguments);
  this.message = message;
}
NoFileAccessError.prototype = Object.create(ExtensionError);

function RestrictedProtocolError(message) {
  Error.apply(this, arguments);
  this.message = message;
}
RestrictedProtocolError.prototype = Object.create(ExtensionError);

function BlockedSiteError(message) {
  Error.apply(this, arguments);
  this.message = message;
}
BlockedSiteError.prototype = Object.create(ExtensionError);

/**
 * Report an error.
 *
 * This currently simply logs the error with console.error().
 * In future we can use this as a place to insert Sentry logging etc.
 *
 * @param {string} context - Describes the context in which the error occurred
 * @param {Error} error - The error which happened.
 */
function report(context, error) {
  console.error(context, error);
}

module.exports = {
  ExtensionError: ExtensionError,
  LocalFileError: LocalFileError,
  NoFileAccessError: NoFileAccessError,
  RestrictedProtocolError: RestrictedProtocolError,
  BlockedSiteError: BlockedSiteError,
  report: report,
};
