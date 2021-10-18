/**
 * EnvironmentFlags provides a facility to modify the appearance or behavior
 * of components on the page depending on the capabilities of the user agent.
 *
 * It adds `env-${flag}` classes to a top-level element in the document to
 * indicate support for scripting, touch input etc. These classes can then be
 * used to modify other elements in the page via descendent selectors.
 *
 * EnvironmentFlags provides hooks to override the detected set of environment
 * features via query-string or fragment parameters in the URL:
 *
 *  "__env__" -  A semi-colon list of environment flags to enable or disable
 *               (if prefixed with "no-"). eg. "__env__=touch"
 *  "nojs=1"  -  Shorthand for "__env__=no-js-capable"
 */
export class EnvironmentFlags {
  /**
   * @param {Element} element - DOM element which environment flags will be added
   *                  to.
   */
  constructor(element) {
    this._element = element;
  }

  /**
   * Return the current value of an environment flag.
   *
   * @param {string} flag
   */
  get(flag) {
    const flagClass = 'env-' + flag;
    return this._element.classList.contains(flagClass);
  }

  /**
   * Set or clear an environment flag.
   *
   * This will add or remove the `env-${flag}` class from the element which
   * contains environment flags.
   *
   * @param {string} flag
   * @param {boolean} on
   */
  set(flag, on) {
    const flagClass = 'env-' + flag;
    if (on) {
      this._element.classList.add(flagClass);
    } else {
      this._element.classList.remove(flagClass);
    }
  }

  /**
   * Detect user agent capabilities and set default flags.
   *
   * This sets the `js-capable` flag but clears it if `ready()` is not called
   * within 5000ms. This can be used to hide elements of the page assuming that
   * they can later be shown via JS but show them again if scripts fail to load.
   *
   * @param {string} [url] - Optional value to use as the URL for flag overrides
   */
  init(url) {
    const JS_LOAD_TIMEOUT = 5000;

    // Mark browser as JS capable
    this.set('js-capable', true);

    // Set a flag to indicate touch support. Useful for browsers that do not
    // support interaction media queries.
    // See http://caniuse.com/#feat=css-media-interaction
    this.set('touch', this._element.ontouchstart);

    // Set an additional flag if scripts fail to load in a reasonable period of
    // time
    this._jsLoadTimeout = setTimeout(() => {
      this.set('js-timeout', true);
    }, JS_LOAD_TIMEOUT);

    // Process flag overrides specified in URL
    const flags = envFlagsFromUrl(
      url || this._element.ownerDocument.location.href
    );
    flags.forEach(flag => {
      if (flag.indexOf('no-') === 0) {
        this.set(flag.slice(3), false);
      } else {
        this.set(flag, true);
      }
    });
  }

  /**
   * Mark the page load as successful.
   */
  ready() {
    if (this._jsLoadTimeout) {
      clearTimeout(this._jsLoadTimeout);
    }
  }
}

/**
 * Extract environment flags from `url`.
 *
 * @param {string} url
 * @return {Array<string>} flags
 */
function envFlagsFromUrl(url) {
  const match = /\b__env__=([^&]+)/.exec(url);
  let flags = [];
  if (match) {
    flags = match[1].split(';');
  }

  // Convenience shorthand to disable JS
  if (url.match(/\bnojs=1\b/)) {
    flags.push('no-js-capable');
  }
  return flags;
}
