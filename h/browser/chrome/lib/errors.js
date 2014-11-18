(function (h) {
  function ExtensionError() {
    Error.apply(this, arguments);
  }
  ExtensionError.prototype = Object.create(Error);

  function LocalFileError() {
    Error.apply(this, arguments);
  }
  LocalFileError.prototype = Object.create(LocalFileError);

  function NoFileAccessError() {
    Error.apply(this, arguments);
  }
  NoFileAccessError.prototype = Object.create(NoFileAccessError);

  h.LocalFileError = LocalFileError;
  h.NoFileAccessError = NoFileAccessError;
})(window.h || (window.h = {}));
