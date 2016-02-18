'use strict';

var escapeHtml  = require('escape-html');

/**
 * Return a nice displayable string representation of a document's title.
 *
 * @returns {String} The document's title preceded on "on " and hyperlinked
 *   to the document's URI. If the document has no http(s) URI then don't
 *   hyperlink the title. If the document has no title then return ''.
 *
 */
module.exports = function documentTitle(document) {
  var title = escapeHtml(document.title || '');
  var uri = escapeHtml(document.uri || '');

  if (uri && !(uri.indexOf('http://') === 0 || uri.indexOf('https://') === 0)) {
    // We only link to http(s) URLs.
    uri = null;
  }

  if (title && uri) {
    return ('on &ldquo;<a target="_blank" href="' + uri + '">' + title +
            '</a>&rdquo;');
  } else if (title) {
    return 'on &ldquo;' + title + '&rdquo;';
  } else {
    return '';
  }
};
