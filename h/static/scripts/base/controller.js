'use strict';

/**
 * Search the DOM tree starting at `el` and return a map of "data-ref" attribute
 * values to elements.
 */
function findRefs(el, map) {
  if (!el.dataset) {
    return map;
  }
  map = map || {};

  var ref = el.dataset.ref;
  if (ref) {
    if (map[ref]) {
      if (Array.isArray(map[ref])) {
        map[ref].push(el);
      } else {
        map[ref] = [map[ref], el];
      }
    } else {
      map[ref] = el;
    }
  }

  for (var i=0; i < el.children.length; i++) {
    var node = el.children[i];
    if (node.nodeType === Node.ELEMENT_NODE) {
      findRefs(node, map);
    }
  }

  return map;
}

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
 *
 * @param {Element} element - The DOM Element to upgrade
 */
function Controller(element) {
  if (!element.controllers) {
    element.controllers = [this];
  } else {
    element.controllers.push(this);
  }

  this.state = {};
  this.element = element;
  this.refs = findRefs(element);
}

/**
 * Set the state of the controller.
 *
 * This will merge `changes` into the current state and call the `update()`
 * method provided by the subclass to update the DOM to match the current state.
 */
Controller.prototype.setState = function (changes) {
  var prevState = this.state;
  this.state = Object.freeze(Object.assign({}, this.state, changes));
  this.update(this.state, prevState);
};

/**
 * Calls update() with the current state.
 *
 * This is useful for controllers where the state is available in the DOM
 * itself, so doesn't need to be maintained internally.
 */
Controller.prototype.forceUpdate = function () {
  this.update(this.state, this.state);
};

module.exports = Controller;
