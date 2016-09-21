'use strict';

/**
 * Search the DOM tree starting at `el` and return a map of "data-ref" attribute
 * values to elements.
 *
 * Multiple controllers may need to refer to the same element, so `data-ref`
 * supports a space-separated list of reference names.
 */
function findRefs(el) {
  var map = {};

  var descendantsWithRef = el.querySelectorAll('[data-ref]');
  for (var i=0; i < descendantsWithRef.length; i++) {
    // Use `Element#getAttribute` rather than `Element#dataset` to support IE 10
    // and avoid https://bugs.webkit.org/show_bug.cgi?id=161454
    var refEl = descendantsWithRef[i];
    var refs = (refEl.getAttribute('data-ref') || '').split(' ');
    refs.forEach(function (ref) {
      map[ref] = refEl;
    });
  }

  return map;
}

/**
 * @typedef {Object} ControllerOptions
 */

/**
 * Base class for controllers that upgrade elements with additional
 * functionality.
 *
 * - Child elements with `data-ref="$name"` attributes are exposed on the
 *   controller as `this.refs.$name`.
 * - The element passed to the controller is exposed via the `element` property
 * - The controllers attached to an element are accessible via the
 *   `element.controllers` array
 *
 * The controller maintains internal state in `this.state`, which can only be
 * updated by calling (`this.setState(changes)`). Whenever the internal state of
 * the controller changes, `this.update()` is called to sync the DOM with this
 * state.
 */
class Controller {
  /**
   * Initialize the controller.
   *
   * @param {Element} element - The DOM Element to upgrade
   * @param {ControllerOptions} [options] - Configuration options for the
   *        controller. Subclasses extend this interface to provide config
   *        specific to that type of controller.
   */
  constructor(element, options = {}) {
    if (!element.controllers) {
      element.controllers = [this];
    } else {
      element.controllers.push(this);
    }

    this.state = {};
    this.element = element;
    this.options = options;
    this.refs = findRefs(element);
  }

  /**
   * Set the state of the controller.
   *
   * This will merge `changes` into the current state and call the `update()`
   * method provided by the subclass to update the DOM to match the current state.
   */
  setState(changes) {
    var prevState = this.state;
    this.state = Object.freeze(Object.assign({}, this.state, changes));
    this.update(this.state, prevState);
  }

  /**
   * Calls update() with the current state.
   *
   * This is useful for controllers where the state is available in the DOM
   * itself, so doesn't need to be maintained internally.
   */
  forceUpdate() {
    this.update(this.state, this.state);
  }
}

module.exports = Controller;
