'use strict';

var annotationIDs = require('../util/annotation-ids');
var settings = require('../settings');

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

  // Parse config from `<script class="js-hypothesis-config">` tags
  try {
    Object.assign(options, settings(window_.document, 'js-hypothesis-config'));
  } catch (err) {
    console.warn('Could not parse settings from js-hypothesis-config tags',
      err);
  }

  // Parse config from `window.hypothesisConfig` function
  if (window_.hasOwnProperty('hypothesisConfig')) {
    if (typeof window_.hypothesisConfig === 'function') {
      Object.assign(options, window_.hypothesisConfig());
    } else {
      throw new TypeError('hypothesisConfig must be a function, see: ' + docs);
    }
  }

  // Extract the direct linked ID from the URL.
  //
  // The Chrome extension or proxy may already have provided this config
  // via a tag injected into the DOM, which avoids the problem where the page's
  // JS rewrites the URL before Hypothesis loads.
  //
  // In environments where the config has not been injected into the DOM,
  // we try to retrieve it from the URL here.
  var directLinkedID = annotationIDs.extractIDFromURL(window_.location.href);
  if (directLinkedID) {
    options.annotations = directLinkedID;
  }
  return options;
}

module.exports = config;
