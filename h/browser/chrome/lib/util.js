function getLastError() {
  if (typeof chrome !== 'undefined' && chrome.extension) {
    return chrome.extension.lastError;
  } else {
    return undefined;
  }
}

/**
 * Converts an async Chrome API into a function
 * which returns a promise.
 *
 * Usage:
 *   var apiFn = promisify(chrome.someModule.aFunction);
 *   apiFn(arg1, arg2)
 *     .then(function (result) { ...handle success  })
 *     .catch(function (err) { ...handle error })
 *
 *
 * @param fn A Chrome API function whose last argument is a callback
 *           which is invoked with the result of the query. When this callback
 *           is invoked, the promise is rejected if chrome.extension.lastError
 *           is set or resolved with the first argument to the callback otherwise.
 */
function promisify(fn) {
  return function () {
    var args = [].slice.call(arguments);
    var result = new Promise(function (resolve, reject) {
      fn.apply(this, args.concat(function (result) {
        var lastError = getLastError();
        if (lastError) {
          reject(lastError);
        } else {
          resolve(result);
        }
      }));
    });
    return result;
  };
}

module.exports = {
  promisify: promisify,
};
