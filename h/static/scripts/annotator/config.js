'use strict';

var annotationIDs = require('../util/annotation-ids');

var docs = 'https://h.readthedocs.org/en/latest/hacking/customized-embedding.html';

/**
 * Reads the Hypothesis configuration from the environment.
 *
 * @param {Window} window_ - The Window object to read config from.
 */
function config(window_) {
  var options = {
    app: window_.
      document.querySelector('link[type="application/annotator+html"]').href,
  };

  // Parse config from `<meta name="hypothesis-config" content="<JSON>">` tags
  var configElement = window_.document
    .querySelector('meta[name="hypothesis-config"]');
  if (configElement) {
    try {
      Object.assign(options, JSON.parse(configElement.content));
    } catch (err) {
      console.warn('Could not parse Hypothesis config from', configElement);
    }
  }

  // Parse config from `window.hypothesisConfig` function
  if (window_.hasOwnProperty('hypothesisConfig')) {
    if (typeof window_.hypothesisConfig === 'function') {
      Object.assign(options, window_.hypothesisConfig());
    } else {
      throw new TypeError('hypothesisConfig must be a function, see: ' + docs);
    }
  }

  var directLinkedID = annotationIDs.extractIDFromURL(window_.location.href);
  if (directLinkedID) {
    options.annotations = directLinkedID;
  }
  return options;
}

module.exports = config;
