var blocklist = (function() {
  'use strict';

  /* Parse the given URL and return an object with its different components.
  *
  * Any or all of the components returned may be undefined.
  * For example for the URL "http://twitter.com" port, path query and anchor
  * will be undefined.
  *
  */
  var parseUrl = function(url) {
    // Regular expression from Douglas Crockford's book
    // JavaScript: The Good Parts.
    var regex = /^(?:([A-Za-z]+):)?(\/{0,3})([0-9.\-A-Za-z]+)(?::(\d+))?(?:\/([^?#]*))?(?:\?([^#]*))?(?:#(.*))?$/;
    var result = regex.exec(url);

    if (result) {
      return {
        scheme: result[1],
        host: result[3],
        port: result[4],
        path: result[5],
        query: result[6],
        anchor: result[7]
      };
    }

    return {
      scheme: undefined,
      host: undefined,
      port: undefined,
      path: undefined,
      query: undefined,
      anchor: undefined
    };
  };

  /* Return true if the given url is blocked by the given blocklist. */
  var isBlocked = function(url, blocklist) {
    url = url || '';

    // Match against the hostname only, so that a pattern like
    // "twitter.com" matches pages like "twitter.com/tag/foo".
    var hostname = parseUrl(url).host;

    if (hostname === undefined) {
      // This happens with things like chrome-devtools:// URLs where there's
      // no host.
      return false;
    }

    var regexSpecialChars = '^$.+?=|\/()[]{}'; //  '*' deliberately omitted.
    for (var pattern in blocklist) {
      if (blocklist.hasOwnProperty(pattern)) {
        // Escape regular expression special characters.
        for (var i = 0; i < regexSpecialChars.length; i++) {
          var c = regexSpecialChars.charAt(i);
          pattern = pattern.replace(c, '\\' + c);
        }

        // Turn * into .* to enable simple patterns like "*.google.com".
        pattern = pattern.replace('*', '.*');

        // Blocklist patterns should match from the start of the URL.
        // This means that "google.com" will _not_ match "mail.google.com",
        // for example. (But "*.google.com" will match it.)
        pattern = '^' + pattern;

        if (hostname.match(pattern)) {
          return true;
        }
      }
    }
    return false;
  };

  return {
    parseUrl: parseUrl,
    isBlocked: isBlocked
  };
})();

if (typeof(window.h) !== 'undefined') {
  // Looks like blocklist.js is being run by the Chrome extension, so add to
  // window.h like the rest of the Chrome extension libs do.
  window.h.blocklist = blocklist;
} else if (typeof(module) !== 'undefined') {
  // Looks like blocklist.js being run by the frontend tests, so export the
  // blocklist using browserify.
  module.exports = blocklist;
} else {
  // Looks like blocklist.js is being run by the bookmarklet, so we don't need
  // to export anything because it gets inlined into embed.js by Jinja2.
}
