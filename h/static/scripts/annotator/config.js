'use strict';

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

  if (window_.hasOwnProperty('hypothesisConfig')) {
    if (typeof window_.hypothesisConfig === 'function') {
      Object.assign(options, window_.hypothesisConfig());
    } else {
      throw new TypeError('hypothesisConfig must be a function, see: ' + docs);
    }
  }

  var annotFragmentMatch = window_.location.hash.match(/^#annotations:(.*)/);
  if (annotFragmentMatch) {
    options.annotations = annotFragmentMatch[1];
  }
  return options;
}

module.exports = config;
