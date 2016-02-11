/** Parse a query string into an object mapping param names to values. */
function parseQuery(query) {
  if (query.charAt(0) === '?') {
    query = query.slice(1);
  }
  return query.split('&').reduce(function (map, entry) {
    var keyValue = entry.split('=').map(function (e) {
      return decodeURIComponent(e);
    });
    map[keyValue[0]] = keyValue[1];
    return map;
  }, {});
}

// Detect the current OS and show approprite help.
chrome.runtime.getPlatformInfo(function (info) {
  var opts = document.querySelectorAll('[data-extension-path]');
  [].forEach.call(opts, function (opt) {
    if (opt.dataset.extensionPath !== info.os) {
      opt.hidden = true;
    }
  });
});

var query = parseQuery(window.location.search);
if (query.message) {
  var errorTextEl = document.querySelector('.js-error-message');
  errorTextEl.textContent = query.message;
}
