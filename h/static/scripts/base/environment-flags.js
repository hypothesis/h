'use strict';

/**
 * EnvironmentFlags provides a facility to modify the appearance or behavior
 * of components on the page depending on the capabilities of the user agent.
 *
 * It adds `env-${flag}` classes to a top-level element in the document to
 * indicate support for scripting, touch input etc. These classes can then be
 * used to modify other elements in the page via descendent selectors.
 *
 * @param {Element} element - DOM element which environment flags will be added
 *                  to.
 */
function EnvironmentFlags(element) {
  this._element = element;
}

EnvironmentFlags.prototype.get = function (flag) {
  var flagClass = 'env-' + flag;
  return this._element.classList.contains(flagClass);
};

/**
 * Set or clear an environment flag.
 *
 * This will add or remove the `env-${flag}` class from the element which
 * contains environment flags.
 */
EnvironmentFlags.prototype.set = function (flag, on) {
  var flagClass = 'env-' + flag;
  if (on) {
    this._element.classList.add(flagClass);
  } else {
    this._element.classList.remove(flagClass);
  }
};

/**
 * Extract environment flags from `url`.
 *
 * @param {string} url
 * @return {Array<string>} flags
 */
function envFlagsFromUrl(url) {
  var match = /\b__env__=([^&]+)/.exec(url);
  var flags = [];
  if (match) {
    flags = match[1].split(';');
  }

  // Convenience shorthand to disable JS
  if (url.match(/\bnojs=1\b/)) {
    flags.push('no-js-capable');
  }
  return flags;
}

/**
 * Detect user agent capabilities and set default flags.
 *
 * This sets the `js-capable` flag but clears it if `ready()` is not called
 * within 5000ms. This can be used to hide elements of the page assuming that
 * they can later be shown via JS but show them again if scripts fail to load.
 *
 * @param {string?} url - Optional value to use as the URL for flag overrides
 */
EnvironmentFlags.prototype.init = function (url) {
  var JS_LOAD_TIMEOUT = 5000;
  var self = this;

  // Mark browser as JS capable
  this.set('js-capable', true);

  // Set a flag to indicate touch support. Useful for browsers that do not
  // support interaction media queries.
  // See http://caniuse.com/#feat=css-media-interaction
  this.set('touch', this._element.ontouchstart);

  // Set an additional flag if scripts fail to load in a reasonable period of
  // time
  this._jsLoadTimeout = setTimeout(function () {
    self.set('js-timeout', true);
  }, JS_LOAD_TIMEOUT);

  // Process flag overrides specified in URL
  var flags = envFlagsFromUrl(url || this._element.ownerDocument.location.href);
  flags.forEach(function (flag) {
    if (flag.indexOf('no-') === 0) {
      self.set(flag.slice(3), false);
    } else {
      self.set(flag, true);
    }
  });
};

/**
 * Mark the page load as successful.
 */
EnvironmentFlags.prototype.ready = function () {
  if (this._jsLoadTimeout) {
    clearTimeout(this._jsLoadTimeout);
  }
};

module.exports = EnvironmentFlags;
