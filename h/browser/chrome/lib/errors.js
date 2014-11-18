(function (h) {
  function ExtensionError() {
    Error.apply(this, arguments);
  }
  ExtensionError.prototype = Object.create(Error);

  function LocalFileError() {
    Error.apply(this, arguments);
  }
  LocalFileError.prototype = Object.create(ExtensionError);

  function NoFileAccessError() {
    Error.apply(this, arguments);
  }
  NoFileAccessError.prototype = Object.create(ExtensionError);

  function RestrictedProtocolError() {
    Error.apply(this, arguments);
  }
  RestrictedProtocolError.prototype = Object.create(ExtensionError);

  h.LocalFileError = LocalFileError;
  h.NoFileAccessError = NoFileAccessError;
  h.RestrictedProtocolError = RestrictedProtocolError;

})(window.h || (window.h = {}));
