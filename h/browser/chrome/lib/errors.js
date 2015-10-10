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

module.exports = {
  ExtensionError: ExtensionError,
  LocalFileError: LocalFileError,
  NoFileAccessError: NoFileAccessError,
  RestrictedProtocolError: RestrictedProtocolError,
  BlockedSiteError: BlockedSiteError,
};
