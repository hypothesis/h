'use strict';

function extractIDFromURL(url) {
  try {
    var annotFragmentMatch = url.match(/#annotations:([A-Za-z0-9_-]+)$/);
    if (annotFragmentMatch) {
      return annotFragmentMatch[1];
    } else {
      return null;
    }
  } catch (err) {
    return null;
  }
}

module.exports = {
  extractIDFromURL: extractIDFromURL,
};
